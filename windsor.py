"""
Windsor.ai connector helpers for Raneen Analytics.
Fetches GA4 data from TWO properties (Web + App) and tags each row
with a `source` column so the dashboard can filter / combine them.
"""

import requests
import pandas as pd
import streamlit as st
from datetime import date, timedelta

from config import WINDSOR_API_KEY, require_windsor_key, redact

WINDSOR_KEY = WINDSOR_API_KEY
WINDSOR_BASE = "https://connectors.windsor.ai/all"

# Windsor account names exactly as they appear in your connected accounts
ACCOUNT_WEB = "Raneen.com"
ACCOUNT_APP = "Raneen Mobile APP (Latest)"


def _preset_to_dates(preset):
    today = date.today()
    mapping = {
        "last_7d": (today - timedelta(days=7), today - timedelta(days=1)),
        "last_14d": (today - timedelta(days=14), today - timedelta(days=1)),
        "last_30d": (today - timedelta(days=30), today - timedelta(days=1)),
        "last_90d": (today - timedelta(days=90), today - timedelta(days=1)),
        "this_month": (today.replace(day=1), today - timedelta(days=1)),
        "last_month": (
            (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            today.replace(day=1) - timedelta(days=1),
        ),
    }
    df, dt = mapping.get(preset, (today - timedelta(days=30), today - timedelta(days=1)))
    return str(df), str(dt)


def _fetch_one_account(account_name, fields, date_from, date_to, timeout=45):
    """Fetch data from Windsor for ONE GA4 account, tag rows with source."""
    # Request account_name as a field so Windsor returns it in the response,
    # enabling the client-side filter below to work correctly.
    fields_clean = list(dict.fromkeys(["account_name"] + [f for f in fields if f != "account_name"]))

    params = {
        "api_key": require_windsor_key(),
        "fields": ",".join(fields_clean),
        "date_from": str(date_from),
        "date_to": str(date_to),
        "account_name": account_name,
    }
    try:
        r = requests.get(WINDSOR_BASE, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        rows = data["data"] if isinstance(data, dict) and "data" in data else (data if isinstance(data, list) else [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        # Filter to only keep rows matching this account — Windsor sometimes
        # returns blended data ignoring the account_name query parameter.
        if "account_name" in df.columns:
            df = df[df["account_name"].astype(str).str.strip() == account_name]
        # Also filter to GA4 datasource only (exclude facebook/other connectors)
        if "datasource" in df.columns:
            df = df[df["datasource"].astype(str).str.strip() == "googleanalytics4"]
        return df
    except requests.exceptions.RequestException as e:
        st.warning(f"Windsor API error for {account_name}: {redact(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Data error for {account_name}: {redact(e)}")
        return pd.DataFrame()


def get_windsor_data(fields, date_preset="last_30d", date_from=None, date_to=None,
                      timeout=45, source="both"):
    """
    Fetch GA4 data combined from Web + App (or just one).

    source: "web" | "app" | "both" (default)
    Adds a `source` column = "web" or "app" so callers can split/filter.
    """
    if not date_from or not date_to:
        date_from, date_to = _preset_to_dates(date_preset)

    frames = []

    if source in ("web", "both"):
        df_web = _fetch_one_account(ACCOUNT_WEB, fields, date_from, date_to, timeout)
        if not df_web.empty:
            df_web["source"] = "web"
            frames.append(df_web)

    if source in ("app", "both"):
        df_app = _fetch_one_account(ACCOUNT_APP, fields, date_from, date_to, timeout)
        if not df_app.empty:
            df_app["source"] = "app"
            frames.append(df_app)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True, sort=False)
    return combined


# ── Formatting helpers (unchanged from original) ────────────────
def safe_num(val, default=0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def fmt_currency(val, decimals=1):
    v = safe_num(val)
    if v >= 1_000_000:
        return f"{v/1_000_000:.{decimals}f}M ج"
    elif v >= 1_000:
        return f"{v/1_000:.{decimals}f}K ج"
    return f"{v:,.0f} ج"


def fmt_number(val, decimals=0):
    v = safe_num(val)
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:,.{decimals}f}"


def fmt_pct(val, decimals=1):
    return f"{safe_num(val):.{decimals}f}%"


def pct_change_color(val):
    v = safe_num(val)
    if v > 0:
        return "#1D9E75"
    elif v < 0:
        return "#D85A30"
    return "#888780"
