"""
Windsor.ai Meta (Facebook/Instagram) Ads connector helper.
Independent module — pulls directly from the Meta/Facebook Ads connector,
NOT from GA4. This means numbers here should match Meta Ads Manager
almost exactly (same source of truth), unlike the GA4-based dashboard
which relies on UTM/session attribution and will show a gap.
"""

import requests
import pandas as pd
import streamlit as st
from datetime import date, timedelta

from config import WINDSOR_API_KEY, require_windsor_key, redact

WINDSOR_KEY = WINDSOR_API_KEY
WINDSOR_BASE = "https://connectors.windsor.ai/facebook"


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


def get_meta_data(fields, date_preset="last_30d", date_from=None, date_to=None, timeout=90, extra_params=None):
    """
    Fetch data directly from the Meta (Facebook) Ads connector on Windsor.

    fields: list of Windsor field IDs (e.g. ["campaign", "spend", "clicks"])
    extra_params: optional dict of additional query params (e.g. level, breakdowns)
    Returns a pandas DataFrame. Empty DataFrame on any failure (never raises),
    so the dashboard can render gracefully and show a clear error message instead.

    IMPORTANT: the Facebook/Meta connector on Windsor rejects date_from/date_to
    with a 400 error (confirmed live) — it only accepts date_preset. So when no
    explicit custom date_from/date_to is given, we send date_preset straight
    through instead of converting it to a date range.
    """
    params = {
        "api_key": require_windsor_key(),
        "fields": ",".join(fields),
    }

    if date_from and date_to:
        # Custom range explicitly requested — try date_from/date_to.
        # (Some Windsor connectors accept this; Facebook may still reject it —
        # the Debug panel in app.py will surface that clearly if so.)
        params["date_from"] = str(date_from)
        params["date_to"] = str(date_to)
    else:
        # Default path — confirmed working live for the Facebook connector.
        params["date_preset"] = date_preset

    if extra_params:
        params.update(extra_params)

    try:
        r = requests.get(WINDSOR_BASE, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        rows = data["data"] if isinstance(data, dict) and "data" in data else (data if isinstance(data, list) else [])
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)
    except requests.exceptions.HTTPError as e:
        # Surface the actual response body — this is what told us about the
        # date_from/date_to 400 error in the first place.
        body = e.response.text[:300] if e.response is not None else ""
        st.session_state.setdefault("_meta_api_errors", []).append(f"{e} | body: {body}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.session_state.setdefault("_meta_api_errors", []).append(redact(e))
        return pd.DataFrame()
    except Exception as e:
        st.session_state.setdefault("_meta_api_errors", []).append(redact(e))
        return pd.DataFrame()


# ── Formatting helpers ───────────────────────────────────────
def safe_num(val, default=0):
    """
    Coerce a Windsor field value to float.
    Some Meta action fields (e.g. purchase_roas, actions_purchase in some
    setups) come back as a nested dict like {"omni_purchase": "1.47"} or a
    list of such dicts instead of a plain number. This extracts the first
    numeric value found in those cases instead of silently returning 0.
    """
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
