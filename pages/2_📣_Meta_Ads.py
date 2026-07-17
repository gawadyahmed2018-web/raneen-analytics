"""
Raneen Meta Ads Dashboard — premium SaaS redesign.
Pulls directly from Meta (Facebook/Instagram) Ads via Windsor.ai.
Numbers here are sourced from Meta itself — NOT GA4.

Visual design matches the Executive Summary / reference: light theme,
soft cards, KPI grid with sparklines, AI performance summary, larger charts,
top campaigns/adsets/ads tables, budget allocation donut, and a daily table.
DATA LOGIC UNCHANGED — only the UI/UX is redesigned.
"""

import io
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from meta_windsor import get_meta_data, safe_num, fmt_currency, fmt_number, fmt_pct

st.set_page_config(page_title="Raneen Meta Ads", page_icon="📣", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════
#  DESIGN TOKENS  (same palette as Executive Summary)
# ══════════════════════════════════════════════════════════
C = {
    "green": "#16B364", "green_soft": "#DCFAE6", "green_dark": "#087443",
    "amber": "#F5A623", "amber_soft": "#FEF0C7", "amber_dark": "#B54708",
    "red": "#F04438", "red_soft": "#FEE4E2", "red_dark": "#B42318",
    "blue": "#2E90FA", "blue_soft": "#DBEAFE", "blue_dark": "#175CD3",
    "purple": "#7A5AF8", "purple_soft": "#EDE9FE", "purple_dark": "#6D28D9",
    "teal": "#14B8A6", "pink": "#EC4899", "orange": "#F97316",
    "meta": "#1877F2",
    "ink": "#0F172A", "ink2": "#475569", "ink3": "#94A0B0",
    "line": "#E9EDF2", "bg": "#F4F6FA", "card": "#FFFFFF",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter','IBM Plex Sans Arabic', sans-serif; }}
#MainMenu, footer {{ visibility: hidden; }}
section[data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
.stApp {{ background: {C['bg']}; }}
.block-container {{ padding: 1rem 1.8rem 2.6rem; max-width: 1520px; }}
section[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid {C['line']}; }}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stTextInput label {{ color: {C['ink2']} !important; font-size: 12px; font-weight: 600; }}

/* top bar */
.topbar {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:16px 22px; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; box-shadow:0 1px 3px rgba(15,23,42,.04); }}
.brand {{ display:flex; align-items:center; gap:13px; }}
.brand-logo {{ width:42px; height:42px; border-radius:11px; background:linear-gradient(135deg,{C['meta']},{C['purple']}); display:flex; align-items:center; justify-content:center; font-size:20px; }}
.brand-t {{ font-size:20px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; display:flex; align-items:center; gap:9px; }}
.brand-s {{ font-size:12px; color:{C['ink3']}; margin-top:1px; }}
.live-dot {{ display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:700; color:{C['green_dark']}; background:{C['green_soft']}; padding:3px 10px; border-radius:100px; }}
.chip {{ background:{C['bg']}; border:1px solid {C['line']}; border-radius:11px; padding:8px 14px; font-size:12.5px; color:{C['ink2']}; font-weight:600; display:inline-flex; align-items:center; gap:7px; }}

/* KPI cards */
.kpi {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:16px; padding:16px 18px; box-shadow:0 1px 2px rgba(15,23,42,.04); transition:transform .16s, box-shadow .16s; height:100%; }}
.kpi:hover {{ transform:translateY(-2px); box-shadow:0 10px 24px rgba(15,23,42,.09); }}
.kpi-top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:9px; }}
.kpi-name {{ font-size:12px; color:{C['ink2']}; font-weight:600; display:flex; align-items:center; gap:6px; }}
.kpi-ico {{ width:26px; height:26px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:13px; }}
.kpi-val {{ font-size:25px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; line-height:1.05; }}
.kpi-unit {{ font-size:13px; font-weight:600; color:{C['ink3']}; margin-left:2px; }}
.kpi-meta {{ display:flex; align-items:center; justify-content:space-between; margin-top:5px; font-size:11.5px; }}
.kpi-sub2 {{ color:{C['ink3']}; font-weight:500; }}
.kpi-delta {{ font-weight:700; display:inline-flex; align-items:center; gap:2px; }}

/* section */
.sec {{ display:flex; align-items:center; gap:10px; margin:22px 0 14px; }}
.sec-t {{ font-size:16px; font-weight:750; color:{C['ink']}; letter-spacing:-.01em; }}
.sec-s {{ font-size:12px; color:{C['ink3']}; margin-left:auto; }}

/* card container */
.card {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:20px; box-shadow:0 1px 3px rgba(15,23,42,.04); height:100%; }}

/* AI summary */
.ai-box {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:20px 22px; box-shadow:0 1px 3px rgba(15,23,42,.04); }}
.ai-title {{ font-size:15px; font-weight:750; color:{C['ink']}; display:flex; align-items:center; gap:8px; }}
.ai-txt {{ font-size:13.5px; color:{C['ink2']}; line-height:1.7; margin-top:12px; }}
.ai-txt b {{ color:{C['ink']}; }}
.pill {{ background:{C['bg']}; border:1px solid {C['line']}; border-radius:12px; padding:11px 13px; }}
.pill-t {{ font-size:11px; color:{C['ink3']}; font-weight:600; display:flex; align-items:center; gap:5px; }}
.pill-v {{ font-size:12.5px; font-weight:700; margin-top:3px; }}

/* tables */
.styled-table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
.styled-table th {{ background:#F8FAFC; color:{C['ink2']}; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:.03em; padding:10px 12px; border-bottom:1px solid {C['line']}; text-align:left; }}
.styled-table td {{ padding:11px 12px; border-bottom:1px solid #F1F5F9; color:{C['ink']}; }}
.styled-table tr:hover td {{ background:rgba(46,144,250,.05); }}
.badge {{ display:inline-block; font-size:10px; padding:3px 9px; border-radius:100px; font-weight:700; }}
.badge-green {{ background:{C['green_soft']}; color:{C['green_dark']}; }}
.badge-amber {{ background:{C['amber_soft']}; color:{C['amber_dark']}; }}
.badge-red {{ background:{C['red_soft']}; color:{C['red_dark']}; }}
.badge-blue {{ background:{C['blue_soft']}; color:{C['blue_dark']}; }}
.legend-row {{ display:flex; align-items:center; gap:8px; margin-bottom:9px; font-size:12.5px; }}
.legend-dot {{ width:9px; height:9px; border-radius:3px; }}
.legend-name {{ color:{C['ink2']}; font-weight:600; flex:1; }}
.legend-pct {{ color:{C['ink']}; font-weight:700; }}
.legend-val {{ color:{C['ink3']}; min-width:60px; text-align:right; }}
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=C["ink2"], size=11),
    margin=dict(l=6, r=6, t=10, b=6),
    xaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False, tickfont=dict(size=10)),
    yaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False, tickfont=dict(size=10)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="white", bordercolor=C["line"], font_size=12),
)


# ══════════════════════════════════════════════════════════
#  HELPERS  (UI only)
# ══════════════════════════════════════════════════════════
def spark(values, color, w=150, h=34):
    vals = [safe_num(v) for v in values if v is not None]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    n = len(vals)
    pts = [((i/(n-1))*w, h - ((v-mn)/rng)*h) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f'<polygon points="0,{h} {line} {w},{h}" fill="{color}" opacity="0.08"/>'
    lx, ly = pts[-1]
    return (
        f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h+3}" preserveAspectRatio="none" style="display:block;">'
        f'{area}<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" fill="{color}"/></svg>'
    )


def kpi(icon, name, value, unit, delta_pct, spark_vals, color, soft, sub="", is_cost=False):
    sp = spark(spark_vals, color) if spark_vals else ""
    delta_html = ""
    if delta_pct is not None:
        good = (delta_pct < 0) if is_cost else (delta_pct >= 0)
        dcol = C["green"] if good else C["red"]
        arrow = "▲" if delta_pct >= 0 else "▼"
        delta_html = f'<span class="kpi-delta" style="color:{dcol}">{arrow} {abs(delta_pct):.1f}%</span>'
    sub_html = f'<span class="kpi-sub2">{sub}</span>' if sub else '<span></span>'
    return (
        f'<div class="kpi"><div class="kpi-top">'
        f'<div class="kpi-name"><span class="kpi-ico" style="background:{soft};color:{color}">{icon}</span>{name}</div>'
        f'</div>'
        f'<div class="kpi-val">{value}<span class="kpi-unit">{unit}</span></div>'
        f'<div class="kpi-meta">{sub_html}{delta_html}</div>'
        f'<div style="margin-top:8px">{sp}</div></div>'
    )


def sec(title, sub=""):
    s = f'<span class="sec-s">{sub}</span>' if sub else ""
    return f'<div class="sec"><div class="sec-t">{title}</div>{s}</div>'


def pct_change(cur, prev):
    if prev == 0:
        return 0.0
    return (cur - prev) / prev * 100


# ══════════════════════════════════════════════════════════
#  SIDEBAR  (unchanged logic)
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📣 Meta Ads")
    st.caption("Meta (Facebook/Instagram) — عبر Windsor.ai")
    st.markdown("---")
    date_preset = st.selectbox(
        "Date Range",
        ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month", "custom"],
        format_func=lambda x: {
            "last_7d": "Last 7 Days", "last_14d": "Last 14 Days", "last_30d": "Last 30 Days",
            "last_90d": "Last 90 Days", "this_month": "This Month", "last_month": "Last Month",
            "custom": "Custom Range",
        }.get(x, x),
    )
    if date_preset == "custom":
        custom_from = st.date_input("From", date.today() - timedelta(days=30))
        custom_to = st.date_input("To", date.today() - timedelta(days=1))

    st.markdown("---")
    # Campaign is the primary level; Ad Sets & Ads load on demand (expanders)
    level_label = "Campaign"
    level = "campaign"

    st.caption("⚠️ الأرقام مصدرها Meta مباشرة — أي فرق عن GA4 طبيعي ومتوقع.")

_d_from, _d_to = (str(custom_from), str(custom_to)) if date_preset == "custom" else (None, None)


# ══════════════════════════════════════════════════════════
#  DATA LOADING  (unchanged logic — confirmed Windsor fields)
# ══════════════════════════════════════════════════════════
BASE_FIELDS = ["date", "account_name", "campaign", "spend", "clicks", "impressions", "reach", "frequency"]
ACTION_FIELDS = ["actions_purchase", "action_values_purchase"]


@st.cache_data(ttl=300, show_spinner="Loading Meta Ads data... قد يستغرق دقيقة في مستوى Ad Set / Ad")
def load_meta_campaigns(preset, d_from, d_to, lvl):
    field_set = list(dict.fromkeys(BASE_FIELDS + [lvl] + ACTION_FIELDS))
    req_timeout = 120 if lvl in ("adset_name", "ad_name") else 60
    df = get_meta_data(field_set, preset, d_from, d_to, timeout=req_timeout)
    return df, False


df_meta, used_fallback = load_meta_campaigns(date_preset, _d_from, _d_to, level)

if df_meta.empty:
    st.markdown('<div class="topbar"><div class="brand"><div class="brand-logo">📣</div>'
                '<div><div class="brand-t">Meta Ads Overview</div>'
                '<div class="brand-s">Real-time performance of your Meta advertising</div></div></div></div>',
                unsafe_allow_html=True)
    st.warning("⚠️ لا توجد بيانات متاحة حالياً من Meta عبر Windsor. تأكد من اتصال حساب Meta على Windsor.ai وأن الفترة فيها بيانات.")
    if "_meta_api_errors" in st.session_state and st.session_state["_meta_api_errors"]:
        with st.expander("🔍 تفاصيل الخطأ"):
            st.write(st.session_state["_meta_api_errors"][-3:])
    st.stop()

# Normalize
NUM_COLS = ["spend", "clicks", "impressions", "reach", "frequency", "actions_purchase", "action_values_purchase"]
for c in NUM_COLS:
    if c in df_meta.columns:
        df_meta[c] = df_meta[c].apply(safe_num)

df_meta["_purchases"] = df_meta["actions_purchase"] if "actions_purchase" in df_meta.columns else 0
df_meta["_purchase_value"] = df_meta["action_values_purchase"] if "action_values_purchase" in df_meta.columns else 0

if level not in df_meta.columns:
    st.error(f"العمود '{level}' غير موجود. الأعمدة المتاحة: {list(df_meta.columns)}")
    st.stop()

# ══════════════════════════════════════════════════════════
#  CAMPAIGN FILTER — one filter, whole page reacts
# ══════════════════════════════════════════════════════════
campaign_list = ["All Campaigns"]
if "campaign" in df_meta.columns:
    camp_spend = df_meta.groupby("campaign")["spend"].sum().sort_values(ascending=False)
    campaign_list += camp_spend.index.tolist()

with st.sidebar:
    st.markdown("---")
    selected_campaign = st.selectbox("🎯 Campaign", campaign_list, key="camp_filter")

# apply the filter to the whole dataset before any calculation
if selected_campaign != "All Campaigns" and "campaign" in df_meta.columns:
    df_meta = df_meta[df_meta["campaign"] == selected_campaign].copy()
    if df_meta.empty:
        st.warning(f"مفيش بيانات للكامبين '{selected_campaign}' في الفترة دي.")
        st.stop()

# ══════════════════════════════════════════════════════════
#  TOTALS  (unchanged calculations)
# ══════════════════════════════════════════════════════════
tot_spend = df_meta["spend"].sum() if "spend" in df_meta.columns else 0
tot_clicks = df_meta["clicks"].sum() if "clicks" in df_meta.columns else 0
tot_impressions = df_meta["impressions"].sum() if "impressions" in df_meta.columns else 0
tot_purchases = df_meta["_purchases"].sum()
tot_purchase_value = df_meta["_purchase_value"].sum()

ctr = (tot_clicks / tot_impressions * 100) if tot_impressions > 0 else 0
cpc = (tot_spend / tot_clicks) if tot_clicks > 0 else 0
cpa = (tot_spend / tot_purchases) if tot_purchases > 0 else 0
roas = (tot_purchase_value / tot_spend) if tot_spend > 0 else 0
aov = (tot_purchase_value / tot_purchases) if tot_purchases > 0 else 0

# daily series (for sparklines + charts) — aggregate by date
if "date" in df_meta.columns:
    daily = df_meta.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.dropna(subset=["date"]).groupby("date", as_index=False).agg({
        "spend": "sum", "clicks": "sum", "impressions": "sum",
        "_purchases": "sum", "_purchase_value": "sum",
    }).sort_values("date")
    daily["roas"] = (daily["_purchase_value"] / daily["spend"]).replace([float("inf")], 0).fillna(0)
    daily["ctr"] = (daily["clicks"] / daily["impressions"] * 100).replace([float("inf")], 0).fillna(0)
    daily["cpa"] = (daily["spend"] / daily["_purchases"]).replace([float("inf")], 0).fillna(0)
    daily["aov"] = (daily["_purchase_value"] / daily["_purchases"]).replace([float("inf")], 0).fillna(0)
else:
    daily = pd.DataFrame()

def dseries(col):
    return daily[col].tolist() if (not daily.empty and col in daily.columns) else []

# previous period (first half vs second half of the daily series, as a lightweight trend proxy)
def split_delta(col):
    if daily.empty or col not in daily.columns or len(daily) < 2:
        return None
    vals = daily[col].tolist()
    mid = len(vals) // 2
    first = sum(vals[:mid]) or 0
    second = sum(vals[mid:]) or 0
    if first == 0:
        return None
    return (second - first) / first * 100

sp_spend = dseries("spend"); sp_rev = dseries("_purchase_value"); sp_roas = dseries("roas")
sp_purch = dseries("_purchases"); sp_cpa = dseries("cpa"); sp_ctr = dseries("ctr"); sp_aov = dseries("aov")


# ══════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════
period_label = {
    "last_7d": "Last 7 Days", "last_14d": "Last 14 Days", "last_30d": "Last 30 Days",
    "last_90d": "Last 90 Days", "this_month": "This Month", "last_month": "Last Month",
    "custom": "Custom Range",
}.get(date_preset, date_preset)

date_span = ""
if not daily.empty:
    date_span = f"{daily['date'].min().date()} → {daily['date'].max().date()}"

st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-logo">📣</div>
    <div>
      <div class="brand-t">Meta Ads Overview <span class="live-dot">● Live</span></div>
      <div class="brand-s">Real-time performance of your Meta advertising</div>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
    <span class="chip">📅 {date_span or period_label}</span>
    <span class="chip">📊 {level_label} level</span>
    <span class="chip" style="color:{C['purple_dark']};background:{C['purple_soft']};border-color:#D9D6FE;">🎯 {selected_campaign[:32]}</span>
    <span class="chip" style="color:{C['blue_dark']};background:{C['blue_soft']};border-color:#B2DDFF;">Ⓜ Meta via Windsor</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 1 — KPI GRID  (7 cards with sparklines, like reference)
# ══════════════════════════════════════════════════════════
k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
with k1:
    st.markdown(kpi("💰", "Spend", fmt_currency(tot_spend), "", split_delta("spend"), sp_spend, C["blue"], C["blue_soft"], is_cost=True), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("💵", "Revenue", fmt_currency(tot_purchase_value), "", split_delta("_purchase_value"), sp_rev, C["green"], C["green_soft"]), unsafe_allow_html=True)
with k3:
    st.markdown(kpi("📈", "ROAS", f"{roas:.2f}", "x", split_delta("roas"), sp_roas, C["purple"], C["purple_soft"]), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("🛒", "Purchases", fmt_number(tot_purchases), "", split_delta("_purchases"), sp_purch, C["teal"], "#CCFBF1"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi("🎯", "CPA", fmt_currency(cpa, 2) if tot_purchases else "—", "", split_delta("cpa"), sp_cpa, C["amber"], C["amber_soft"], is_cost=True), unsafe_allow_html=True)
with k6:
    st.markdown(kpi("🖱", "CTR", f"{ctr:.2f}", "%", split_delta("ctr"), sp_ctr, C["blue"], C["blue_soft"]), unsafe_allow_html=True)
with k7:
    st.markdown(kpi("🧾", "AOV", fmt_currency(aov, 2) if tot_purchases else "—", "", split_delta("aov"), sp_aov, C["pink"], "#FCE7F3"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 2 — AI PERFORMANCE SUMMARY
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
ai_l, ai_r = st.columns([2, 1])

with ai_l:
    # top campaign by roas (with meaningful spend)
    grp = df_meta.groupby(level, as_index=False).agg({"spend": "sum", "_purchases": "sum", "_purchase_value": "sum"})
    grp = grp[grp["spend"] > 0].copy()
    grp["roas"] = (grp["_purchase_value"] / grp["spend"]).replace([float("inf")], 0)
    top_perf = grp[grp["spend"] >= grp["spend"].median()].sort_values("roas", ascending=False)
    best_name = top_perf.iloc[0][level] if not top_perf.empty else "—"
    best_roas = top_perf.iloc[0]["roas"] if not top_perf.empty else 0
    worst = top_perf.sort_values("roas").iloc[0] if not top_perf.empty else None

    spend_delta = split_delta("spend") or 0
    roas_delta = split_delta("roas") or 0
    summary = (
        f'Meta delivered <b>{fmt_number(tot_purchases)}</b> purchases at a blended ROAS of <b>{roas:.2f}x</b> '
        f'on <b>{fmt_currency(tot_spend)}</b> spend. '
        f'Top performer is <b>{best_name}</b> with a ROAS of <b>{best_roas:.2f}x</b>. '
    )
    if roas_delta >= 0:
        summary += f'Overall ROAS improved <b>{abs(roas_delta):.1f}%</b> across the period.'
    else:
        summary += f'Overall ROAS declined <b>{abs(roas_delta):.1f}%</b> — review underperforming {level_label.lower()}s.'

    def pill(icon, title, val, color):
        return f'<div class="pill"><div class="pill-t">{icon} {title}</div><div class="pill-v" style="color:{color}">{val}</div></div>'

    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-title">🤖 AI Performance Summary <span class="badge badge-blue">Beta</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-txt">{summary}</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1: st.markdown(pill("🏆", "Top Performer", f"{best_name}", C["green"]), unsafe_allow_html=True)
    with p2: st.markdown(pill("📈", "Best ROAS", f"{best_roas:.2f}x", C["blue"]), unsafe_allow_html=True)
    with p3: st.markdown(pill("💸", "Blended CPA", fmt_currency(cpa, 2) if tot_purchases else "—", C["amber"]), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with ai_r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:6px;">Efficiency Snapshot</div>', unsafe_allow_html=True)
    for label, val, color in [
        ("CPC (Cost per Click)", fmt_currency(cpc, 2), C["blue"]),
        ("CTR (Click-through)", f"{ctr:.2f}%", C["purple"]),
        ("Impressions", fmt_number(tot_impressions), C["teal"]),
        ("Clicks", fmt_number(tot_clicks), C["green"]),
    ]:
        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid {C["line"]};">'
                    f'<span style="font-size:12.5px;color:{C["ink2"]};font-weight:600;">{label}</span>'
                    f'<span style="font-size:14px;color:{color};font-weight:800;">{val}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 3 — Performance Over Time  +  ROAS Over Time
# ══════════════════════════════════════════════════════════
st.markdown(sec("📊 Performance Trends"), unsafe_allow_html=True)
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:8px;">Spend vs Revenue Over Time</div>', unsafe_allow_html=True)
    if not daily.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["spend"], name="Spend", mode="lines+markers",
                                 line=dict(color=C["blue"], width=2.5), marker=dict(size=4)))
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["_purchase_value"], name="Revenue", mode="lines+markers",
                                 line=dict(color=C["green"], width=2.5), marker=dict(size=4),
                                 fill="tonexty", fillcolor="rgba(22,179,100,.06)"))
        fig.update_layout(**PLOT, height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with ch2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:8px;">ROAS Over Time</div>', unsafe_allow_html=True)
    if not daily.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["roas"], name="ROAS", mode="lines+markers",
                                 line=dict(color=C["purple"], width=2.5), marker=dict(size=5, color=C["purple"]),
                                 fill="tozeroy", fillcolor="rgba(122,90,248,.07)"))
        fig.add_hline(y=roas, line_dash="dash", line_color=C["ink3"], annotation_text=f"Avg {roas:.2f}x", annotation_position="top left")
        fig.update_layout(**PLOT, height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 4 — Top {level}  +  Budget Allocation donut
# ══════════════════════════════════════════════════════════
st.markdown(sec(f"🏆 Top {level_label}s", "بالأداء"), unsafe_allow_html=True)
t_l, t_r = st.columns([1.7, 1])

grp_full = df_meta.groupby(level, as_index=False).agg({
    "spend": "sum", "clicks": "sum", "impressions": "sum",
    "_purchases": "sum", "_purchase_value": "sum",
})
grp_full = grp_full[grp_full["spend"] > 0].copy()
grp_full["roas"] = (grp_full["_purchase_value"] / grp_full["spend"]).replace([float("inf")], 0)
grp_full["cpa"] = (grp_full["spend"] / grp_full["_purchases"]).replace([float("inf")], 0)
grp_full["ctr"] = (grp_full["clicks"] / grp_full["impressions"] * 100).replace([float("inf")], 0)
grp_full = grp_full.sort_values("spend", ascending=False)

with t_l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    rows = []
    for _, r in grp_full.head(10).iterrows():
        rr = r["roas"]
        badge = '<span class="badge badge-green">قوي</span>' if rr >= 3 else ('<span class="badge badge-amber">متوسط</span>' if rr >= 1 else '<span class="badge badge-red">ضعيف</span>')
        rows.append(
            f"<tr><td style='font-weight:600;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{r[level]}</td>"
            f"<td>{fmt_currency(r['spend'])}</td>"
            f"<td>{fmt_number(r['_purchases'])}</td>"
            f"<td>{fmt_currency(r['_purchase_value'])}</td>"
            f"<td>{rr:.2f}x</td>"
            f"<td>{fmt_currency(r['cpa'],2) if r['_purchases']>0 else '—'}</td>"
            f"<td>{badge}</td></tr>"
        )
    st.markdown(
        "<table class='styled-table'><thead><tr><th>" + level_label + "</th><th>Spend</th><th>Purch.</th>"
        "<th>Revenue</th><th>ROAS</th><th>CPA</th><th></th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with t_r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:8px;">Budget Allocation</div>', unsafe_allow_html=True)
    top_alloc = grp_full.head(5).copy()
    others = grp_full.iloc[5:]["spend"].sum() if len(grp_full) > 5 else 0
    palette = [C["blue"], C["green"], C["orange"], C["purple"], C["teal"], C["ink3"]]
    labels = top_alloc[level].tolist()
    values = top_alloc["spend"].tolist()
    if others > 0:
        labels.append("Other"); values.append(others)
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.64,
                           marker=dict(colors=palette[:len(labels)], line=dict(color="#fff", width=2)),
                           textinfo="none", sort=False))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=170, margin=dict(l=0,r=0,t=0,b=0),
                      annotations=[dict(text=f"<b>{fmt_currency(tot_spend)}</b><br><span style='font-size:9px;color:{C['ink3']}'>Total Spend</span>",
                                        x=0.5, y=0.5, font_size=13, showarrow=False, font_color=C["ink"])])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    leg = ""
    for i, (lab, val) in enumerate(zip(labels, values)):
        p = (val/tot_spend*100) if tot_spend else 0
        short = (lab[:16] + "…") if len(str(lab)) > 17 else lab
        leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{palette[i%len(palette)]}"></span>'
                f'<span class="legend-name">{short}</span><span class="legend-pct">{p:.0f}%</span>'
                f'<span class="legend-val">{fmt_currency(val)}</span></div>')
    st.markdown(leg, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 4.5 — Ad Sets & Ads breakdown  (lazy, load on demand)
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner="Loading breakdown...")
def load_level(preset, d_from, d_to, lvl, camp_filter):
    field_set = list(dict.fromkeys(BASE_FIELDS + [lvl] + ACTION_FIELDS))
    req_timeout = 120 if lvl in ("adset_name", "ad_name") else 60
    df = get_meta_data(field_set, preset, d_from, d_to, timeout=req_timeout)
    if df.empty:
        return df
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    df["_purchases"] = df["actions_purchase"] if "actions_purchase" in df.columns else 0
    df["_purchase_value"] = df["action_values_purchase"] if "action_values_purchase" in df.columns else 0
    if camp_filter != "All Campaigns" and "campaign" in df.columns:
        df = df[df["campaign"] == camp_filter]
    return df


def render_level_table(df_lvl, lvl_col, lvl_name):
    if df_lvl.empty or lvl_col not in df_lvl.columns:
        st.info(f"مفيش بيانات على مستوى {lvl_name} في الفترة/الكامبين المختار.")
        return
    g = df_lvl.groupby(lvl_col, as_index=False).agg({
        "spend": "sum", "clicks": "sum", "impressions": "sum",
        "_purchases": "sum", "_purchase_value": "sum",
    })
    g = g[g["spend"] > 0].copy()
    g["roas"] = (g["_purchase_value"] / g["spend"]).replace([float("inf")], 0)
    g["cpa"] = (g["spend"] / g["_purchases"]).replace([float("inf")], 0)
    g["ctr"] = (g["clicks"] / g["impressions"] * 100).replace([float("inf")], 0)
    g = g.sort_values("spend", ascending=False)
    rows = []
    for _, r in g.head(25).iterrows():
        rr = r["roas"]
        badge = '<span class="badge badge-green">قوي</span>' if rr >= 3 else ('<span class="badge badge-amber">متوسط</span>' if rr >= 1 else '<span class="badge badge-red">ضعيف</span>')
        rows.append(
            f"<tr><td style='font-weight:600;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{r[lvl_col]}</td>"
            f"<td>{fmt_currency(r['spend'])}</td><td>{fmt_number(r['_purchases'])}</td>"
            f"<td>{fmt_currency(r['_purchase_value'])}</td><td>{rr:.2f}x</td>"
            f"<td>{fmt_currency(r['cpa'],2) if r['_purchases']>0 else '—'}</td>"
            f"<td>{r['ctr']:.2f}%</td><td>{badge}</td></tr>"
        )
    st.markdown(
        "<table class='styled-table'><thead><tr><th>" + lvl_name + "</th><th>Spend</th><th>Purch.</th>"
        "<th>Revenue</th><th>ROAS</th><th>CPA</th><th>CTR</th><th></th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>",
        unsafe_allow_html=True,
    )

st.markdown(sec("🔍 Ad Sets & Ads Breakdown", "اضغط لعرض التفاصيل — تتحمّل عند الطلب"), unsafe_allow_html=True)

with st.expander("📂 Ad Sets Performance"):
    df_adset = load_level(date_preset, _d_from, _d_to, "adset_name", selected_campaign)
    render_level_table(df_adset, "adset_name", "Ad Set")

with st.expander("📄 Ads Performance"):
    df_ad = load_level(date_preset, _d_from, _d_to, "ad_name", selected_campaign)
    render_level_table(df_ad, "ad_name", "Ad")


# ══════════════════════════════════════════════════════════
#  AUDIENCE & PLACEMENT INSIGHTS  (lazy breakdowns)
#  Confirmed Windsor fields: publisher_platform, platform_position,
#  age, gender, country, region — all return live data.
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner="Loading breakdown...")
def load_breakdown(preset, d_from, d_to, extra_fields, camp_filter):
    field_set = list(dict.fromkeys(["date", "campaign", "spend"] + extra_fields + ACTION_FIELDS))
    df = get_meta_data(field_set, preset, d_from, d_to, timeout=90)
    if df.empty:
        return df
    for c in ["spend", "actions_purchase", "action_values_purchase"]:
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    df["_purchases"] = df["actions_purchase"] if "actions_purchase" in df.columns else 0
    df["_purchase_value"] = df["action_values_purchase"] if "action_values_purchase" in df.columns else 0
    if camp_filter != "All Campaigns" and "campaign" in df.columns:
        df = df[df["campaign"] == camp_filter]
    return df


def breakdown_agg(df_b, dim):
    """Aggregate a breakdown by dimension, compute ROAS, sort by spend."""
    if df_b.empty or dim not in df_b.columns:
        return pd.DataFrame()
    g = df_b.groupby(dim, as_index=False).agg({"spend": "sum", "_purchases": "sum", "_purchase_value": "sum"})
    g = g[g["spend"] > 0].copy()
    g["roas"] = (g["_purchase_value"] / g["spend"]).replace([float("inf")], 0)
    return g.sort_values("spend", ascending=False)


def hbar_chart(g, dim, color, height=280, top=8):
    """Horizontal bar of spend by dimension, with ROAS in hover."""
    gg = g.head(top).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=gg["spend"], y=gg[dim].astype(str), orientation="h",
        marker_color=color,
        text=[f"{fmt_currency(s)} · {r:.1f}x" for s, r in zip(gg["spend"], gg["roas"])],
        textposition="auto",
        hovertemplate="%{y}<br>Spend: %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(**PLOT, height=height)
    return fig


st.markdown(sec("🎯 Audience & Placement Insights", "من أين تأتي النتائج — تتحمّل عند الطلب"), unsafe_allow_html=True)

# ── Placements ──
with st.expander("📍 Placements — أين تظهر إعلاناتك (Platform + Position)"):
    df_pl = load_breakdown(date_preset, _d_from, _d_to, ["publisher_platform", "platform_position"], selected_campaign)
    if df_pl.empty:
        st.info("مفيش بيانات placements في الفترة/الكامبين المختار.")
    else:
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{C["ink2"]};margin-bottom:6px;">حسب المنصة (Platform)</div>', unsafe_allow_html=True)
            g_plat = breakdown_agg(df_pl, "publisher_platform")
            if not g_plat.empty:
                st.plotly_chart(hbar_chart(g_plat, "publisher_platform", C["blue"], height=240), use_container_width=True, config={"displayModeBar": False})
        with pc2:
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{C["ink2"]};margin-bottom:6px;">حسب الموضع (Position)</div>', unsafe_allow_html=True)
            g_pos = breakdown_agg(df_pl, "platform_position")
            if not g_pos.empty:
                st.plotly_chart(hbar_chart(g_pos, "platform_position", C["purple"], height=240), use_container_width=True, config={"displayModeBar": False})

# ── Demographics (Age + Gender) ──
with st.expander("👥 Demographics — العمر والنوع (Age + Gender)"):
    df_dg = load_breakdown(date_preset, _d_from, _d_to, ["age", "gender"], selected_campaign)
    if df_dg.empty:
        st.info("مفيش بيانات ديموغرافية في الفترة/الكامبين المختار.")
    else:
        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{C["ink2"]};margin-bottom:6px;">حسب العمر (Age)</div>', unsafe_allow_html=True)
            g_age = breakdown_agg(df_dg, "age").sort_values("age")
            if not g_age.empty:
                fig = go.Figure(go.Bar(x=g_age["age"].astype(str), y=g_age["spend"], marker_color=C["teal"],
                                       text=[f"{r:.1f}x" for r in g_age["roas"]], textposition="outside",
                                       hovertemplate="Age %{x}<br>Spend: %{y:,.0f}<extra></extra>"))
                fig.update_layout(**PLOT, height=260)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with dc2:
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{C["ink2"]};margin-bottom:6px;">حسب النوع (Gender)</div>', unsafe_allow_html=True)
            g_gen = breakdown_agg(df_dg, "gender")
            if not g_gen.empty:
                gmap = {"male": "ذكور", "female": "إناث", "unknown": "غير محدد"}
                colors_g = {"male": C["blue"], "female": C["pink"], "unknown": C["ink3"]}
                fig = go.Figure(go.Pie(
                    labels=[gmap.get(x, x) for x in g_gen["gender"]], values=g_gen["spend"], hole=0.6,
                    marker=dict(colors=[colors_g.get(x, C["ink3"]) for x in g_gen["gender"]], line=dict(color="#fff", width=2)),
                    textinfo="label+percent", textfont=dict(size=12),
                ))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=260, margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        # Age × Gender heat-style table
        if "age" in df_dg.columns and "gender" in df_dg.columns:
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{C["ink2"]};margin:10px 0 6px;">العمر × النوع (Spend)</div>', unsafe_allow_html=True)
            pivot = df_dg.groupby(["age", "gender"])["spend"].sum().reset_index()
            pivot_t = pivot.pivot(index="age", columns="gender", values="spend").fillna(0)
            st.dataframe(pivot_t, use_container_width=True)

# ── Geography ──
with st.expander("🗺️ Geography — التوزيع الجغرافي (Region)"):
    df_geo = load_breakdown(date_preset, _d_from, _d_to, ["country", "region"], selected_campaign)
    if df_geo.empty:
        st.info("مفيش بيانات جغرافية في الفترة/الكامبين المختار.")
    else:
        g_reg = breakdown_agg(df_geo, "region")
        if not g_reg.empty:
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{C["ink2"]};margin-bottom:6px;">أعلى المحافظات بالإنفاق (Top Regions)</div>', unsafe_allow_html=True)
            st.plotly_chart(hbar_chart(g_reg, "region", C["orange"], height=380, top=15), use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════
#  ROW 5 — Performance by Day  (table)
# ══════════════════════════════════════════════════════════
if not daily.empty:
    st.markdown(sec("📋 Performance by Day"), unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    tbl = daily.sort_values("date", ascending=False).copy()
    tbl["date"] = tbl["date"].dt.strftime("%b %d, %Y")
    tbl_show = tbl[["date", "spend", "impressions", "clicks", "ctr", "_purchases", "cpa", "_purchase_value", "roas"]].copy()
    st.dataframe(
        tbl_show, use_container_width=True, height=380, hide_index=True,
        column_config={
            "date": st.column_config.TextColumn("Date"),
            "spend": st.column_config.NumberColumn("Spend", format="$%,.0f"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%,d"),
            "clicks": st.column_config.NumberColumn("Clicks", format="%,d"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "_purchases": st.column_config.NumberColumn("Purchases", format="%,d"),
            "cpa": st.column_config.NumberColumn("CPA", format="$%.2f"),
            "_purchase_value": st.column_config.NumberColumn("Revenue", format="$%,.0f"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2fx"),
        },
    )
    buf = io.BytesIO()
    tbl_show.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("📥 Download CSV", buf.getvalue(), f"meta_{level}_performance.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("💡 الأرقام مصدرها Meta مباشرة عبر Windsor.ai — أي فرق عن GA4 طبيعي (اختلاف نماذج الـ attribution).")
