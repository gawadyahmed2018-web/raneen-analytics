"""
Raneen Analytics Hub — Home Page
A unified command center summarizing all data sources:
GA4 (Web + App), Meta Ads, and Google Ads — all via Windsor.ai.
Each source has its own detailed page in the sidebar.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from windsor import get_windsor_data, safe_num, fmt_currency, fmt_number, fmt_pct
from meta_windsor import get_meta_data
from google_ads_windsor import get_google_ads_data

st.set_page_config(page_title="Raneen Analytics Hub", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans Arabic', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1400px; }
.hub-card { background: #FFFFFF; border: 1px solid #E2E6EA; border-radius: 16px; padding: 24px; margin-bottom: 16px; transition: all .2s; height: 100%; }
.hub-card:hover { border-color: #3266AD; box-shadow: 0 4px 20px rgba(50,102,173,0.08); }
.source-icon { font-size: 32px; margin-bottom: 12px; }
.source-title { font-size: 18px; font-weight: 700; color: #1A1A2E; margin-bottom: 4px; }
.source-sub { font-size: 12px; color: #9A9A8E; margin-bottom: 18px; }
.metric-row { display: flex; justify-content: space-between; padding: 8px 0; border-top: 1px solid #F0F2F5; }
.metric-label { font-size: 12px; color: #73726C; }
.metric-value { font-size: 14px; font-weight: 600; color: #1A1A2E; }
.big-metric { font-size: 28px; font-weight: 700; color: #1A1A2E; }
.hub-header { display: flex; align-items: center; gap: 14px; padding: 10px 0 24px; border-bottom: 1px solid #E2E6EA; margin-bottom: 28px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Analytics Hub")
    st.caption("مركز التحكم الموحّد — Raneen")
    st.markdown("---")
    date_preset = st.selectbox(
        "Date Range",
        ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month"],
        format_func=lambda x: {
            "last_7d": "Last 7 Days", "last_14d": "Last 14 Days", "last_30d": "Last 30 Days",
            "last_90d": "Last 90 Days", "this_month": "This Month", "last_month": "Last Month",
        }.get(x, x),
    )
    st.markdown("---")
    st.markdown("**الصفحات:**")
    st.markdown("🌐 GA4 Web + App")
    st.markdown("📣 Meta Ads")
    st.markdown("🔵 Google Ads")
    st.caption("اختر صفحة من القائمة فوق للتفاصيل الكاملة")

# ── Header ───────────────────────────────────────────────
st.markdown("""
<div class="hub-header">
  <span style="font-size:36px;">🎯</span>
  <div>
    <div style="font-size:26px; font-weight:800; color:#1A1A2E;">Raneen Analytics Hub</div>
    <div style="font-size:12px; color:#9A9A8E;">مركز موحّد لكل مصادر البيانات — GA4 · Meta Ads · Google Ads</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Prominent link to the Executive Summary (profitability overview)
st.page_link("pages/0_🎯_Executive_Summary.py", label="🎯 افتح الملخص التنفيذي — الربحية والأداء مقابل التارجت", icon="📊")
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)


# ── Data loaders (summary level only) ────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_ga4_summary(preset):
    df = get_windsor_data(
        ["date", "sessions", "purchase_revenue", "transactions"],
        preset, source="both",
    )
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_meta_summary(preset):
    return get_meta_data(
        ["date", "spend", "actions_purchase", "action_values_purchase", "clicks", "impressions"],
        preset,
    )


@st.cache_data(ttl=300, show_spinner=False)
def load_gads_summary(preset):
    return get_google_ads_data(
        ["date", "spend", "conversions", "conversions_value", "clicks", "impressions"],
        preset,
    )


with st.spinner("⏳ جاري تحميل ملخص كل المصادر..."):
    df_ga4 = load_ga4_summary(date_preset)
    df_meta = load_meta_summary(date_preset)
    df_gads = load_gads_summary(date_preset)

# ── Compute summaries ────────────────────────────────────
# GA4
ga4_sessions = safe_num(df_ga4["sessions"].sum()) if not df_ga4.empty and "sessions" in df_ga4.columns else 0
ga4_revenue = safe_num(df_ga4["purchase_revenue"].sum()) if not df_ga4.empty and "purchase_revenue" in df_ga4.columns else 0
ga4_orders = safe_num(df_ga4["transactions"].sum()) if not df_ga4.empty and "transactions" in df_ga4.columns else 0

# Meta
meta_spend = meta_conv = meta_conv_val = 0
if not df_meta.empty:
    for c in ["spend", "actions_purchase", "action_values_purchase"]:
        if c in df_meta.columns:
            df_meta[c] = df_meta[c].apply(safe_num)
    meta_spend = df_meta["spend"].sum() if "spend" in df_meta.columns else 0
    meta_conv = df_meta["actions_purchase"].sum() if "actions_purchase" in df_meta.columns else 0
    meta_conv_val = df_meta["action_values_purchase"].sum() if "action_values_purchase" in df_meta.columns else 0
meta_roas = (meta_conv_val / meta_spend) if meta_spend > 0 else 0

# Google Ads
gads_spend = gads_conv = gads_conv_val = 0
if not df_gads.empty:
    for c in ["spend", "conversions", "conversions_value"]:
        if c in df_gads.columns:
            df_gads[c] = df_gads[c].apply(safe_num)
    gads_spend = df_gads["spend"].sum() if "spend" in df_gads.columns else 0
    gads_conv = df_gads["conversions"].sum() if "conversions" in df_gads.columns else 0
    gads_conv_val = df_gads["conversions_value"].sum() if "conversions_value" in df_gads.columns else 0
gads_roas = (gads_conv_val / gads_spend) if gads_spend > 0 else 0

# Combined ad spend
total_ad_spend = meta_spend + gads_spend

# ── Top summary strip ────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(f'<div class="hub-card" style="text-align:center;"><div class="metric-label">إجمالي المبيعات (GA4)</div><div class="big-metric" style="color:#1D9E75;">{fmt_currency(ga4_revenue)}</div><div class="source-sub">{fmt_number(ga4_orders)} طلب</div></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div class="hub-card" style="text-align:center;"><div class="metric-label">إجمالي الإنفاق الإعلاني</div><div class="big-metric" style="color:#D85A30;">{fmt_currency(total_ad_spend)}</div><div class="source-sub">Meta + Google</div></div>', unsafe_allow_html=True)
with s3:
    blended_roas = (ga4_revenue / total_ad_spend) if total_ad_spend > 0 else 0
    st.markdown(f'<div class="hub-card" style="text-align:center;"><div class="metric-label">Blended ROAS</div><div class="big-metric" style="color:#7F77DD;">{blended_roas:.2f}x</div><div class="source-sub">مبيعات ÷ إنفاق</div></div>', unsafe_allow_html=True)
with s4:
    st.markdown(f'<div class="hub-card" style="text-align:center;"><div class="metric-label">Sessions (GA4)</div><div class="big-metric" style="color:#3266AD;">{fmt_number(ga4_sessions)}</div><div class="source-sub">Web + App</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Source cards ─────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="hub-card">
      <div class="source-icon">🌐</div>
      <div class="source-title">GA4 — Web + App</div>
      <div class="source-sub">Google Analytics 4</div>
      <div class="metric-row"><span class="metric-label">Revenue</span><span class="metric-value">{fmt_currency(ga4_revenue)}</span></div>
      <div class="metric-row"><span class="metric-label">Orders</span><span class="metric-value">{fmt_number(ga4_orders)}</span></div>
      <div class="metric-row"><span class="metric-label">Sessions</span><span class="metric-value">{fmt_number(ga4_sessions)}</span></div>
      <div class="metric-row"><span class="metric-label">AOV</span><span class="metric-value">{fmt_currency(ga4_revenue/ga4_orders if ga4_orders else 0, 0)}</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_🌐_GA4_Web_App.py", label="افتح تفاصيل GA4 ←", icon="🌐")

with col2:
    st.markdown(f"""
    <div class="hub-card">
      <div class="source-icon">📣</div>
      <div class="source-title">Meta Ads</div>
      <div class="source-sub">Facebook + Instagram</div>
      <div class="metric-row"><span class="metric-label">Spend</span><span class="metric-value">{fmt_currency(meta_spend)}</span></div>
      <div class="metric-row"><span class="metric-label">Purchases</span><span class="metric-value">{fmt_number(meta_conv)}</span></div>
      <div class="metric-row"><span class="metric-label">Conv. Value</span><span class="metric-value">{fmt_currency(meta_conv_val)}</span></div>
      <div class="metric-row"><span class="metric-label">ROAS</span><span class="metric-value">{meta_roas:.2f}x</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_📣_Meta_Ads.py", label="افتح تفاصيل Meta ←", icon="📣")

with col3:
    st.markdown(f"""
    <div class="hub-card">
      <div class="source-icon">🔵</div>
      <div class="source-title">Google Ads</div>
      <div class="source-sub">Search + Shopping + PMax</div>
      <div class="metric-row"><span class="metric-label">Spend</span><span class="metric-value">{fmt_currency(gads_spend)}</span></div>
      <div class="metric-row"><span class="metric-label">Conversions</span><span class="metric-value">{fmt_number(gads_conv)}</span></div>
      <div class="metric-row"><span class="metric-label">Conv. Value</span><span class="metric-value">{fmt_currency(gads_conv_val)}</span></div>
      <div class="metric-row"><span class="metric-label">ROAS</span><span class="metric-value">{gads_roas:.2f}x</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_🔵_Google_Ads.py", label="افتح تفاصيل Google Ads ←", icon="🔵")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.caption("💡 كل الأرقام هنا ملخصة. افتح صفحة أي مصدر من القائمة الجانبية للتفاصيل الكاملة، الرسوم البيانية، والتصدير.")
