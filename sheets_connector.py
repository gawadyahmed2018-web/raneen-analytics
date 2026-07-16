"""
Google Sheets connector for the Executive Summary page.
Reads the published "Target & Sales Overview" sheet live as CSV.
"""

import pandas as pd
import streamlit as st

# Published CSV export URL (derived from the pubhtml link)
SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vToNIxR30TywAr5X3Ok7EOtRoMVnHGttVb6AxUZpkUT8161rVVGCIZ542n9K_SEjsAzGo3yWFUuTuUr"
    "/pub?gid=559443792&single=true&output=csv"
)

NUM_COLS = [
    "Dollar Rate", "Facebook Spending (USD)", "Facebook Spending",
    "Google Base Amount (USD)", "Google Extra Amount", "Google Spending",
    "SMS Spending", "TikTok Spending", "Criteo Spending", "Extra Spending",
    "Coupons", "Total Spending", "Spending Target",
    "Received Sales", "Received Target", "Confirmed Sales", "Confirmed Target",
    "Retail Confirmed Sales", "Retail Confirmed Target",
    "Marketplace Confirmed Sales", "Marketplace Confirmed Target",
    "Saved Spending", "No. of Orders", "AOV", "Days Remaining Each Month",
]


@st.cache_data(ttl=300, show_spinner="Loading sales & spending data...")
def load_sales_sheet():
    """Load and clean the sales overview sheet. Returns a cleaned DataFrame."""
    try:
        df = pd.read_csv(SHEET_CSV_URL)
    except Exception as e:
        st.session_state.setdefault("_sheet_errors", []).append(str(e))
        return pd.DataFrame()

    # Parse date
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")

    # Clean numeric columns (strip commas)
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.strip(), errors="coerce")

    return df


def safe_num(val, default=0):
    try:
        if val is None or pd.isna(val):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def fmt_egp(val, decimals=1):
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
