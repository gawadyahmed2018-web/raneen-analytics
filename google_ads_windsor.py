"""
Windsor.ai Google Ads connector helper.
Pulls directly from the Google Ads connector — confirmed field names:
date, campaign, clicks, spend, impressions, conversions, conversions_value
"""

import requests
import pandas as pd
import streamlit as st
from datetime import date, timedelta

from config import WINDSOR_API_KEY, require_windsor_key, redact

WINDSOR_KEY = WINDSOR_API_KEY
WINDSOR_BASE = "https://connectors.windsor.ai/google_ads"


def preset_to_range(preset):
    """Return (date_from, date_to) for a preset."""
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
    return mapping.get(preset, (today - timedelta(days=30), today - timedelta(days=1)))


def previous_period(date_from, date_to):
    """Given a date range, return the immediately preceding range of equal length."""
    d_from = pd.to_datetime(date_from).date()
    d_to = pd.to_datetime(date_to).date()
    length = (d_to - d_from).days + 1
    prev_to = d_from - timedelta(days=1)
    prev_from = prev_to - timedelta(days=length - 1)
    return str(prev_from), str(prev_to)


def get_google_ads_data(fields, date_preset="last_30d", date_from=None, date_to=None, timeout=60):
    """Fetch data from the Google Ads connector. Returns empty DataFrame on failure."""
    params = {
        "api_key": require_windsor_key(),
        "fields": ",".join(fields),
    }
    if date_from and date_to:
        params["date_from"] = str(date_from)
        params["date_to"] = str(date_to)
    else:
        params["date_preset"] = date_preset

    try:
        r = requests.get(WINDSOR_BASE, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        rows = data["data"] if isinstance(data, dict) and "data" in data else (data if isinstance(data, list) else [])
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)
    except requests.exceptions.RequestException as e:
        st.session_state.setdefault("_gads_errors", []).append(redact(e))
        return pd.DataFrame()
    except Exception as e:
        st.session_state.setdefault("_gads_errors", []).append(redact(e))
        return pd.DataFrame()


def safe_num(val, default=0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        for v in val.values():
            n = safe_num(v, None)
            if n is not None:
                return n
        return default
    if isinstance(val, (list, tuple)):
        for item in val:
            n = safe_num(item, None)
            if n is not None:
                return n
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def fmt_currency(val, decimals=1):
    v = safe_num(val)
    if v >= 1_000_000:
        return f"${v/1_000_000:.{decimals}f}M"
    elif v >= 1_000:
        return f"${v/1_000:.{decimals}f}K"
    return f"${v:,.0f}"


def fmt_number(val, decimals=0):
    v = safe_num(val)
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:,.{decimals}f}"


def fmt_pct(val, decimals=2):
    return f"{safe_num(val):.{decimals}f}%"
