"""
Central configuration — credentials are read from secrets, never hardcoded.

Set these in Streamlit Cloud → your app → Settings → Secrets:

    WINDSOR_API_KEY = "your-new-windsor-key"
    SALES_SHEET_CSV_URL = "https://docs.google.com/.../pub?gid=...&single=true&output=csv"

For local development, put the same lines in `.streamlit/secrets.toml`
and make sure that file is listed in .gitignore (never commit it).
"""

import os
import re

import streamlit as st

# Fallback used only if SALES_SHEET_CSV_URL is not configured, so the
# dashboard keeps working while secrets are being set up.
_DEFAULT_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vToNIxR30TywAr5X3Ok7EOtRoMVnHGttVb6AxUZpkUT8161rVVGCIZ542n9K_SEjsAzGo3yWFUuTuUr"
    "/pub?gid=559443792&single=true&output=csv"
)


def _secret(name, default=""):
    """Read a value from st.secrets, then the environment, then the default."""
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        # No secrets file configured (e.g. plain local run) — fall through.
        pass
    return str(os.environ.get(name, default)).strip()


WINDSOR_API_KEY = _secret("WINDSOR_API_KEY")
SALES_SHEET_CSV_URL = _secret("SALES_SHEET_CSV_URL", _DEFAULT_SHEET_CSV_URL)


def require_windsor_key():
    """Return the Windsor key, or stop the app with a clear message if missing."""
    if not WINDSOR_API_KEY:
        st.error(
            "⚠️ **مفتاح Windsor غير مضبوط.**\n\n"
            "روح على Streamlit Cloud ← التطبيق ← **Settings → Secrets** وضيف السطر ده:\n\n"
            "```toml\nWINDSOR_API_KEY = \"مفتاحك-الجديد\"\n```\n\n"
            "وللتشغيل المحلي، حط نفس السطر في ملف `.streamlit/secrets.toml`."
        )
        st.stop()
    return WINDSOR_API_KEY


def redact(text):
    """Strip credentials out of any text before it is shown to a user.

    Network errors from `requests` embed the full request URL, which includes
    the api_key query parameter. Never surface that raw.
    """
    s = str(text)
    if WINDSOR_API_KEY:
        s = s.replace(WINDSOR_API_KEY, "***REDACTED***")
    # catch any api_key=... pattern, even a stale or differently-sourced key
    s = re.sub(r"(api_key=)[^&\s'\"]+", r"\1***REDACTED***", s, flags=re.IGNORECASE)
    return s
