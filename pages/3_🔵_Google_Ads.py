"""
Raneen Google Ads — Command Center.
Source: Google Ads via Windsor.ai (all fields confirmed live).

Sections: account/type tabs, AI summary, spend pacing, KPI grid with sparklines,
revenue-vs-spend, conversion funnel, search-query intelligence, keywords,
device performance, impression share, hourly heatmap, top campaigns, daily table.
"""

import io
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from google_ads_windsor import (
    get_google_ads_data, safe_num, fmt_currency, fmt_number, fmt_pct,
    preset_to_range, previous_period,
)

st.set_page_config(page_title="Raneen Google Ads", page_icon="🔵", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════
#  DESIGN TOKENS (same system as Executive / Meta)
# ══════════════════════════════════════════════════════════
C = {
    "green": "#16B364", "green_soft": "#DCFAE6", "green_dark": "#087443",
    "amber": "#F5A623", "amber_soft": "#FEF0C7", "amber_dark": "#B54708",
    "red": "#F04438", "red_soft": "#FEE4E2", "red_dark": "#B42318",
    "blue": "#2E90FA", "blue_soft": "#DBEAFE", "blue_dark": "#175CD3",
    "indigo": "#4F46E5", "indigo_soft": "#E0E7FF",
    "purple": "#7A5AF8", "purple_soft": "#EDE9FE", "purple_dark": "#6D28D9",
    "teal": "#14B8A6", "pink": "#EC4899", "orange": "#F97316",
    "ink": "#0F172A", "ink2": "#475569", "ink3": "#94A0B0",
    "line": "#E9EDF2", "bg": "#F4F6FA", "card": "#FFFFFF",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family:'Inter','IBM Plex Sans Arabic',sans-serif; }}
#MainMenu, footer {{ visibility:hidden; }}
section[data-testid="stHeader"] {{ background:rgba(0,0,0,0); }}
.stApp {{ background:{C['bg']}; }}
.block-container {{ padding:1rem 1.8rem 2.6rem; max-width:1560px; }}
section[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid {C['line']}; }}
section[data-testid="stSidebar"] label {{ color:{C['ink2']} !important; font-size:12px; font-weight:600; }}

.topbar {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:16px 22px;
  margin-bottom:14px; display:flex; align-items:center; justify-content:space-between; gap:16px;
  flex-wrap:wrap; box-shadow:0 1px 3px rgba(15,23,42,.04); }}
.brand {{ display:flex; align-items:center; gap:13px; }}
.brand-logo {{ width:42px; height:42px; border-radius:11px; background:linear-gradient(135deg,{C['blue']},{C['indigo']});
  display:flex; align-items:center; justify-content:center; font-size:20px; }}
.brand-t {{ font-size:20px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; display:flex; align-items:center; gap:9px; }}
.brand-s {{ font-size:12px; color:{C['ink3']}; margin-top:1px; }}
.live-dot {{ display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:700;
  color:{C['green_dark']}; background:{C['green_soft']}; padding:3px 10px; border-radius:100px; }}
.chip {{ background:{C['bg']}; border:1px solid {C['line']}; border-radius:11px; padding:8px 14px;
  font-size:12.5px; color:{C['ink2']}; font-weight:600; display:inline-flex; align-items:center; gap:7px; }}

.kpi {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:16px; padding:16px 18px;
  box-shadow:0 1px 2px rgba(15,23,42,.04); transition:transform .16s, box-shadow .16s; height:100%; }}
.kpi:hover {{ transform:translateY(-2px); box-shadow:0 10px 24px rgba(15,23,42,.09); }}
.kpi-name {{ font-size:12px; color:{C['ink2']}; font-weight:600; display:flex; align-items:center; gap:6px; margin-bottom:9px; }}
.kpi-ico {{ width:26px; height:26px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:13px; }}
.kpi-val {{ font-size:25px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; line-height:1.05; }}
.kpi-unit {{ font-size:13px; font-weight:600; color:{C['ink3']}; margin-left:2px; }}
.kpi-meta {{ display:flex; align-items:center; justify-content:space-between; margin-top:5px; font-size:11.5px; }}
.kpi-sub2 {{ color:{C['ink3']}; font-weight:500; }}
.kpi-delta {{ font-weight:700; }}

.sec {{ display:flex; align-items:center; gap:10px; margin:20px 0 12px; }}
.sec-t {{ font-size:16px; font-weight:750; color:{C['ink']}; letter-spacing:-.01em; }}
.sec-s {{ font-size:12px; color:{C['ink3']}; margin-left:auto; }}

.card {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:20px;
  box-shadow:0 1px 3px rgba(15,23,42,.04); height:100%; }}
.card-t {{ font-size:14px; font-weight:750; color:{C['ink']}; margin-bottom:10px; }}

.ai-row {{ display:flex; align-items:flex-start; gap:10px; padding:9px 0; font-size:13px; color:{C['ink2']}; line-height:1.6; }}
.ai-row b {{ color:{C['ink']}; }}
.ai-ico {{ color:{C['indigo']}; font-size:13px; }}

.styled-table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
.styled-table th {{ background:#F8FAFC; color:{C['ink2']}; font-weight:600; font-size:11px; text-transform:uppercase;
  letter-spacing:.03em; padding:10px 12px; border-bottom:1px solid {C['line']}; text-align:left; }}
.styled-table td {{ padding:10px 12px; border-bottom:1px solid #F1F5F9; color:{C['ink']}; }}
.styled-table tr:hover td {{ background:rgba(46,144,250,.05); }}
.badge {{ display:inline-block; font-size:10px; padding:3px 9px; border-radius:100px; font-weight:700; }}
.badge-green {{ background:{C['green_soft']}; color:{C['green_dark']}; }}
.badge-amber {{ background:{C['amber_soft']}; color:{C['amber_dark']}; }}
.badge-red {{ background:{C['red_soft']}; color:{C['red_dark']}; }}
.badge-blue {{ background:{C['blue_soft']}; color:{C['blue_dark']}; }}
.badge-purple {{ background:{C['purple_soft']}; color:{C['purple_dark']}; }}
.legend-row {{ display:flex; align-items:center; gap:8px; margin-bottom:9px; font-size:12.5px; }}
.legend-dot {{ width:9px; height:9px; border-radius:3px; }}
.legend-name {{ color:{C['ink2']}; font-weight:600; flex:1; }}
.legend-pct {{ color:{C['ink']}; font-weight:700; }}
.legend-val {{ color:{C['ink3']}; min-width:62px; text-align:right; }}
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
#  HELPERS
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
    lx, ly = pts[-1]
    return (
        f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h+3}" preserveAspectRatio="none" style="display:block;">'
        f'<polygon points="0,{h} {line} {w},{h}" fill="{color}" opacity="0.08"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
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
        f'<div class="kpi">'
        f'<div class="kpi-name"><span class="kpi-ico" style="background:{soft};color:{color}">{icon}</span>{name}</div>'
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
#  SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔵 Google Ads")
    st.caption("Google Ads — عبر Windsor.ai")
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
    st.caption("💡 كل الأرقام مصدرها Google Ads مباشرة.")

d_from, d_to = preset_to_range(date_preset)
prev_from, prev_to = previous_period(d_from, d_to)

CORE_FIELDS = ["date", "account_name", "campaign", "campaign_type", "clicks", "spend",
               "impressions", "conversions", "conversions_value"]


@st.cache_data(ttl=300, show_spinner="Loading Google Ads data...")
def load_core(dfrom, dto):
    df = get_google_ads_data(CORE_FIELDS, date_from=dfrom, date_to=dto, timeout=90)
    if df.empty:
        return df
    for c in ["clicks", "spend", "impressions", "conversions", "conversions_value"]:
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_extra(dfrom, dto, extra_fields):
    """Load a secondary breakdown (device / IS / hourly / keywords / search terms)."""
    fields = list(dict.fromkeys(["date", "campaign", "spend"] + extra_fields))
    df = get_google_ads_data(fields, date_from=dfrom, date_to=dto, timeout=90)
    if df.empty:
        return df
    for c in ["spend", "clicks", "impressions", "conversions", "conversions_value",
              "search_impression_share", "search_budget_lost_impression_share",
              "search_rank_lost_impression_share", "all_conversions", "view_through_conversions"]:
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    return df


df_all = load_core(str(d_from), str(d_to))
df_prev_all = load_core(prev_from, prev_to)

if df_all.empty:
    st.markdown('<div class="topbar"><div class="brand"><div class="brand-logo">🔵</div>'
                '<div><div class="brand-t">Google Ads — Command Center</div>'
                '<div class="brand-s">Real-time performance overview</div></div></div></div>',
                unsafe_allow_html=True)
    st.warning("⚠️ لا توجد بيانات من Google Ads في الفترة دي. تأكد من الاتصال على Windsor.ai.")
    if "_gads_errors" in st.session_state and st.session_state["_gads_errors"]:
        with st.expander("🔍 تفاصيل الخطأ"):
            st.write(st.session_state["_gads_errors"][-3:])
    st.stop()


# ══════════════════════════════════════════════════════════
#  ACCOUNT / TYPE TABS  (Search · PMax · All)
# ══════════════════════════════════════════════════════════
TYPE_TABS = {
    "🔵 All": None,
    "🔍 Search": "SEARCH",
    "⚡ Performance Max": "PERFORMANCE_MAX",
    "📢 Demand Gen": "DEMAND_GEN",
    "📱 App": "MULTI_CHANNEL",
}
available_types = set(df_all["campaign_type"].astype(str).str.upper().unique()) if "campaign_type" in df_all.columns else set()
tab_names = [k for k, v in TYPE_TABS.items() if v is None or v in available_types]

active_tab = st.radio("النوع", tab_names, horizontal=True, key="type_tab", label_visibility="collapsed")
type_filter = TYPE_TABS[active_tab]


def apply_type(df):
    if df.empty or type_filter is None or "campaign_type" not in df.columns:
        return df
    return df[df["campaign_type"].astype(str).str.upper() == type_filter]


df = apply_type(df_all).copy()
df_prev = apply_type(df_prev_all).copy()

if df.empty:
    st.info(f"مفيش بيانات لـ {active_tab} في الفترة دي.")
    st.stop()

# campaign multi-filter (top of page)
campaign_list = df.groupby("campaign")["spend"].sum().sort_values(ascending=False).index.tolist() if "campaign" in df.columns else []
selected_campaigns = st.multiselect(
    "🎯 فلتر الكامبينات — اختر واحدة أو أكتر (فاضي = الكل)",
    campaign_list, default=[], key="gads_camp_filter", placeholder="كل الكامبينات",
)
if selected_campaigns and "campaign" in df.columns:
    df = df[df["campaign"].isin(selected_campaigns)]
    df_prev = df_prev[df_prev["campaign"].isin(selected_campaigns)] if "campaign" in df_prev.columns else df_prev
    if df.empty:
        st.warning("مفيش بيانات للكامبينات المختارة.")
        st.stop()

campaign_label = ("All Campaigns" if not selected_campaigns
                  else selected_campaigns[0] if len(selected_campaigns) == 1
                  else f"{len(selected_campaigns)} campaigns")


# ══════════════════════════════════════════════════════════
#  TOTALS
# ══════════════════════════════════════════════════════════
def tot(frame, col):
    return frame[col].sum() if (not frame.empty and col in frame.columns) else 0

t_spend = tot(df, "spend");   t_clicks = tot(df, "clicks");   t_impr = tot(df, "impressions")
t_conv = tot(df, "conversions"); t_val = tot(df, "conversions_value")
p_spend = tot(df_prev, "spend"); p_clicks = tot(df_prev, "clicks"); p_impr = tot(df_prev, "impressions")
p_conv = tot(df_prev, "conversions"); p_val = tot(df_prev, "conversions_value")

roas = (t_val / t_spend) if t_spend else 0
p_roas = (p_val / p_spend) if p_spend else 0
cpa = (t_spend / t_conv) if t_conv else 0
p_cpa = (p_spend / p_conv) if p_conv else 0
cpc = (t_spend / t_clicks) if t_clicks else 0
p_cpc = (p_spend / p_clicks) if p_clicks else 0
ctr = (t_clicks / t_impr * 100) if t_impr else 0
p_ctr = (p_clicks / p_impr * 100) if p_impr else 0
cvr = (t_conv / t_clicks * 100) if t_clicks else 0
aov = (t_val / t_conv) if t_conv else 0

# daily series
if "date" in df.columns:
    daily = df.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.dropna(subset=["date"]).groupby("date", as_index=False).agg({
        "spend": "sum", "clicks": "sum", "impressions": "sum",
        "conversions": "sum", "conversions_value": "sum",
    }).sort_values("date")
    daily["roas"] = (daily["conversions_value"] / daily["spend"]).replace([float("inf")], 0).fillna(0)
    daily["cpa"] = (daily["spend"] / daily["conversions"]).replace([float("inf")], 0).fillna(0)
else:
    daily = pd.DataFrame()


def dser(col):
    return daily[col].tolist() if (not daily.empty and col in daily.columns) else []


# ══════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-logo">🔵</div>
    <div>
      <div class="brand-t">Google Ads — Command Center <span class="live-dot">● Live</span></div>
      <div class="brand-s">Real-time performance overview of your Google advertising</div>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
    <span class="chip">📅 {d_from} → {d_to}</span>
    <span class="chip">🔄 Compare: {prev_from} → {prev_to}</span>
    <span class="chip" style="color:{C['purple_dark']};background:{C['purple_soft']};border-color:#D9D6FE;">🎯 {campaign_label[:30]}</span>
    <span class="chip" style="color:{C['blue_dark']};background:{C['blue_soft']};border-color:#B2DDFF;">{active_tab}</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 1 — AI EXECUTIVE SUMMARY  +  SPEND PACING
# ══════════════════════════════════════════════════════════
r1l, r1r = st.columns([1.9, 1])

with r1l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-t">✨ AI Executive Summary</div>', unsafe_allow_html=True)

    lines = []
    d_roas = pct_change(roas, p_roas)
    lines.append(f'<b>ROAS is {roas:.2f}x</b>, {"up" if d_roas>=0 else "down"} <b>{abs(d_roas):.1f}%</b> vs the previous period.')
    d_cpa = pct_change(cpa, p_cpa)
    if t_conv:
        lines.append(f'<b>CPA is {fmt_currency(cpa,2)}</b> — {"improved" if d_cpa<0 else "increased"} by <b>{abs(d_cpa):.1f}%</b>' +
                     (" and needs attention." if d_cpa > 10 else "."))
    # best / worst campaign by roas among meaningful spenders
    g = df.groupby("campaign", as_index=False).agg({"spend": "sum", "conversions": "sum", "conversions_value": "sum"})
    g = g[g["spend"] > 0].copy()
    g["roas"] = (g["conversions_value"] / g["spend"]).replace([float("inf")], 0)
    big = g[g["spend"] >= g["spend"].median()] if len(g) > 1 else g
    if not big.empty:
        best = big.sort_values("roas", ascending=False).iloc[0]
        worst = big.sort_values("roas").iloc[0]
        lines.append(f'Top performer: <b>{best["campaign"]}</b> at <b>{best["roas"]:.2f}x</b> ROAS.')
        if worst["roas"] < roas * 0.6:
            lines.append(f'<b>{worst["campaign"]}</b> is underperforming at <b>{worst["roas"]:.2f}x</b> — review budget allocation.')
    d_spend = pct_change(t_spend, p_spend)
    lines.append(f'Spend <b>{fmt_currency(t_spend)}</b> ({d_spend:+.1f}%) generated <b>{fmt_number(t_conv)}</b> conversions worth <b>{fmt_currency(t_val)}</b>.')

    for ln in lines:
        st.markdown(f'<div class="ai-row"><span class="ai-ico">✦</span><span>{ln}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r1r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-t">Spend Pacing</div>', unsafe_allow_html=True)
    # pace = elapsed share of the selected window (projection basis, no budget field in the API)
    n_days = max(len(daily), 1)
    window_days = (pd.to_datetime(d_to) - pd.to_datetime(d_from)).days + 1
    elapsed_pct = min(n_days / window_days * 100, 100) if window_days else 0
    daily_burn = t_spend / n_days if n_days else 0
    projected = daily_burn * window_days
    pcol = C["indigo"]
    fig = go.Figure(go.Pie(values=[elapsed_pct, max(100-elapsed_pct, 0)], hole=0.72,
                           marker=dict(colors=[pcol, C["line"]]), textinfo="none", sort=False, direction="clockwise"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=150, margin=dict(l=0,r=0,t=0,b=0),
                      annotations=[dict(text=f"<b>{elapsed_pct:.0f}%</b><br><span style='font-size:9px;color:{C['ink3']}'>of period</span>",
                                        x=0.5, y=0.5, font_size=20, showarrow=False, font_color=C["ink"])])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f'<div style="font-size:11.5px;color:{C["ink2"]};line-height:2;">'
        f'<div style="display:flex;justify-content:space-between;"><span>Spent</span><b>{fmt_currency(t_spend)}</b></div>'
        f'<div style="display:flex;justify-content:space-between;"><span>Daily Burn</span><b>{fmt_currency(daily_burn,2)}</b></div>'
        f'<div style="display:flex;justify-content:space-between;"><span>Projected (full window)</span><b>{fmt_currency(projected)}</b></div>'
        f'<div style="display:flex;justify-content:space-between;"><span>Days with data</span><b>{n_days} / {window_days}</b></div></div>',
        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 2 — KPI GRID
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.markdown(kpi("💰", "Spend", fmt_currency(t_spend), "", pct_change(t_spend, p_spend), dser("spend"),
                    C["blue"], C["blue_soft"], is_cost=True), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("🖱", "Clicks", fmt_number(t_clicks), "", pct_change(t_clicks, p_clicks), dser("clicks"),
                    C["indigo"], C["indigo_soft"], sub=f"CTR {ctr:.2f}%"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi("🎯", "Conversions", fmt_number(t_conv), "", pct_change(t_conv, p_conv), dser("conversions"),
                    C["teal"], "#CCFBF1", sub=f"CVR {cvr:.2f}%"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("💵", "Revenue", fmt_currency(t_val), "", pct_change(t_val, p_val), dser("conversions_value"),
                    C["green"], C["green_soft"]), unsafe_allow_html=True)
with k5:
    st.markdown(kpi("📈", "ROAS", f"{roas:.2f}", "x", pct_change(roas, p_roas), dser("roas"),
                    C["purple"], C["purple_soft"]), unsafe_allow_html=True)
with k6:
    st.markdown(kpi("💸", "CPA", fmt_currency(cpa, 2) if t_conv else "—", "", pct_change(cpa, p_cpa), dser("cpa"),
                    C["amber"], C["amber_soft"], is_cost=True), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 3 — REVENUE vs SPEND  +  CONVERSION FUNNEL
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
r3l, r3r = st.columns([1.45, 1])

with r3l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Revenue vs Spend</div>', unsafe_allow_html=True)
    if not daily.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["conversions_value"], name="Revenue", mode="lines+markers",
                                 line=dict(color=C["indigo"], width=2.5), marker=dict(size=5),
                                 hovertemplate="Revenue: %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["spend"], name="Spend", mode="lines+markers",
                                 line=dict(color=C["green"], width=2.5), marker=dict(size=5),
                                 hovertemplate="Spend: %{y:,.0f}<extra></extra>"))
        fig.update_layout(**PLOT, height=330, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r3r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Conversion Funnel</div>', unsafe_allow_html=True)
    stages = [("Impressions", t_impr), ("Clicks", t_clicks), ("Conversions", t_conv)]
    stages = [(n, v) for n, v in stages if v > 0]
    if len(stages) >= 2:
        fig = go.Figure(go.Funnel(
            y=[s[0] for s in stages], x=[s[1] for s in stages],
            textposition="inside", textinfo="value+percent initial",
            marker=dict(color=[C["blue"], C["indigo"], C["purple"]][:len(stages)]),
            connector=dict(line=dict(color=C["line"], width=1)),
        ))
        fig.update_layout(**{k: v for k, v in PLOT.items() if k in ("paper_bgcolor", "plot_bgcolor", "font")},
                          height=210, margin=dict(l=10, r=10, t=6, b=6))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        # step drop-offs
        for i in range(1, len(stages)):
            pn, pv = stages[i-1]; cn, cv = stages[i]
            conv = (cv / pv * 100) if pv else 0
            drop = 100 - conv
            dcol = C["green"] if drop <= 40 else (C["amber"] if drop <= 90 else C["red"])
            st.markdown(
                f'<div style="margin-bottom:9px;"><div style="display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:3px;">'
                f'<span style="color:{C["ink2"]};font-weight:600;">{pn} → {cn}</span>'
                f'<span style="color:{dcol};font-weight:800;">{conv:.2f}%</span></div>'
                f'<div style="height:7px;background:{C["line"]};border-radius:100px;overflow:hidden;">'
                f'<div style="width:{min(conv,100)}%;height:100%;background:{dcol};border-radius:100px;"></div></div></div>',
                unsafe_allow_html=True)
    else:
        st.info("مفيش بيانات كافية للفانل.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 4 — SEARCH QUERY INTELLIGENCE  +  DEVICE PERFORMANCE
# ══════════════════════════════════════════════════════════
st.markdown(sec("🔍 Search Intelligence & Devices"), unsafe_allow_html=True)
r4l, r4r = st.columns([1.7, 1])

with r4l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Search Query Intelligence — أكثر ما يبحث عنه العملاء</div>', unsafe_allow_html=True)
    df_sq = load_extra(str(d_from), str(d_to), ["search_term", "clicks", "conversions", "conversions_value"])
    if selected_campaigns and not df_sq.empty and "campaign" in df_sq.columns:
        df_sq = df_sq[df_sq["campaign"].isin(selected_campaigns)]
    if df_sq.empty or "search_term" not in df_sq.columns:
        st.info("مفيش بيانات search terms في الفترة دي.")
    else:
        g = df_sq.groupby("search_term", as_index=False).agg({
            "spend": "sum", "clicks": "sum", "conversions": "sum", "conversions_value": "sum"})
        g = g[(g["spend"] > 0) | (g["clicks"] > 0)].copy()
        g["roas"] = (g["conversions_value"] / g["spend"]).replace([float("inf")], 0).fillna(0)
        g["cvr"] = (g["conversions"] / g["clicks"] * 100).replace([float("inf")], 0).fillna(0)
        g = g.sort_values("spend", ascending=False)
        rows = []
        for _, r in g.head(15).iterrows():
            rr = r["roas"]
            badge = ('<span class="badge badge-green">قوي</span>' if rr >= 3 else
                     '<span class="badge badge-amber">متوسط</span>' if rr >= 1 else
                     '<span class="badge badge-red">ضعيف</span>')
            rows.append(
                f"<tr><td style='font-weight:600;max-width:230px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{r['search_term']}</td>"
                f"<td>{fmt_number(r['clicks'])}</td><td>{fmt_currency(r['spend'],2)}</td>"
                f"<td>{fmt_currency(r['conversions_value'])}</td><td>{rr:.2f}x</td>"
                f"<td>{r['cvr']:.1f}%</td><td>{badge}</td></tr>")
        st.markdown(
            "<table class='styled-table'><thead><tr><th>Search Term</th><th>Clicks</th><th>Cost</th>"
            "<th>Revenue</th><th>ROAS</th><th>CVR</th><th></th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        # negative keyword candidates: spend, no conversions
        neg = g[(g["conversions"] == 0) & (g["spend"] > 0)].sort_values("spend", ascending=False)
        if not neg.empty:
            wasted = neg["spend"].sum()
            names = " · ".join(neg.head(5)["search_term"].astype(str).tolist())
            st.markdown(
                f'<div style="margin-top:12px;background:{C["red_soft"]};border:1px solid #FECDCA;border-radius:12px;padding:11px 14px;">'
                f'<div style="font-size:11.5px;color:{C["red_dark"]};font-weight:700;">🚫 Negative Keyword Candidates — إنفاق بدون تحويل: {fmt_currency(wasted,2)}</div>'
                f'<div style="font-size:11.5px;color:{C["ink2"]};margin-top:4px;">{names}</div></div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Device Performance</div>', unsafe_allow_html=True)
    df_dev = load_extra(str(d_from), str(d_to), ["device", "clicks", "conversions", "conversions_value"])
    if selected_campaigns and not df_dev.empty and "campaign" in df_dev.columns:
        df_dev = df_dev[df_dev["campaign"].isin(selected_campaigns)]
    if df_dev.empty or "device" not in df_dev.columns:
        st.info("مفيش بيانات أجهزة.")
    else:
        g = df_dev.groupby("device", as_index=False).agg({
            "spend": "sum", "clicks": "sum", "conversions": "sum", "conversions_value": "sum"})
        g = g[g["spend"] > 0].copy()
        g["roas"] = (g["conversions_value"] / g["spend"]).replace([float("inf")], 0).fillna(0)
        g = g.sort_values("spend", ascending=False)
        dev_colors = {"MOBILE": C["blue"], "DESKTOP": C["indigo"], "TABLET": C["teal"], "CONNECTED_TV": C["purple"]}
        dev_names = {"MOBILE": "Mobile", "DESKTOP": "Desktop", "TABLET": "Tablet", "CONNECTED_TV": "Connected TV"}
        fig = go.Figure(go.Pie(
            labels=[dev_names.get(x, x) for x in g["device"]], values=g["spend"], hole=0.66,
            marker=dict(colors=[dev_colors.get(x, C["ink3"]) for x in g["device"]], line=dict(color="#fff", width=2)),
            textinfo="none", sort=False,
            hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=170, margin=dict(l=0,r=0,t=0,b=0),
                          annotations=[dict(text=f"<b>{fmt_currency(g['spend'].sum())}</b><br><span style='font-size:9px;color:{C['ink3']}'>Spend</span>",
                                            x=0.5, y=0.5, font_size=13, showarrow=False, font_color=C["ink"])])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        tot_dev = g["spend"].sum()
        leg = ""
        for _, r in g.iterrows():
            p = (r["spend"]/tot_dev*100) if tot_dev else 0
            leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{dev_colors.get(r["device"], C["ink3"])}"></span>'
                    f'<span class="legend-name">{dev_names.get(r["device"], r["device"])}</span>'
                    f'<span class="legend-pct">{p:.1f}%</span>'
                    f'<span class="legend-val">{fmt_currency(r["spend"])} · {r["roas"]:.1f}x</span></div>')
        st.markdown(leg, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 5 — IMPRESSION SHARE  +  HOURLY HEATMAP
# ══════════════════════════════════════════════════════════
st.markdown(sec("📊 Visibility & Timing"), unsafe_allow_html=True)
r5l, r5r = st.columns([1, 1.7])

with r5l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Impression Share</div>', unsafe_allow_html=True)
    df_is = load_extra(str(d_from), str(d_to),
                       ["impressions", "search_impression_share",
                        "search_budget_lost_impression_share", "search_rank_lost_impression_share"])
    if selected_campaigns and not df_is.empty and "campaign" in df_is.columns:
        df_is = df_is[df_is["campaign"].isin(selected_campaigns)]
    is_cols = ["search_impression_share", "search_budget_lost_impression_share", "search_rank_lost_impression_share"]
    if df_is.empty or not all(c in df_is.columns for c in is_cols):
        st.info("مفيش بيانات Impression Share (متاحة لحملات Search فقط).")
    else:
        w = df_is["impressions"] if "impressions" in df_is.columns else df_is["spend"]
        w = w.fillna(0)
        valid = df_is[is_cols].notna().all(axis=1) & (w > 0)
        if valid.sum() == 0:
            st.info("مفيش بيانات Impression Share للفلتر الحالي.")
        else:
            ww = w[valid]
            owned = (df_is.loc[valid, "search_impression_share"] * ww).sum() / ww.sum() * 100
            lost_b = (df_is.loc[valid, "search_budget_lost_impression_share"] * ww).sum() / ww.sum() * 100
            lost_r = (df_is.loc[valid, "search_rank_lost_impression_share"] * ww).sum() / ww.sum() * 100
            parts = [("Owned IS", owned, C["indigo"]), ("Lost IS (Budget)", lost_b, C["teal"]), ("Lost IS (Rank)", lost_r, C["amber"])]
            fig = go.Figure(go.Pie(labels=[p[0] for p in parts], values=[max(p[1], 0) for p in parts], hole=0.66,
                                   marker=dict(colors=[p[2] for p in parts], line=dict(color="#fff", width=2)),
                                   textinfo="none", sort=False,
                                   hovertemplate="%{label}<br>%{percent}<extra></extra>"))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=170, margin=dict(l=0,r=0,t=0,b=0),
                              annotations=[dict(text=f"<b>{owned:.1f}%</b><br><span style='font-size:9px;color:{C['ink3']}'>Owned</span>",
                                                x=0.5, y=0.5, font_size=16, showarrow=False, font_color=C["ink"])])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            leg = ""
            for nm, v, cl in parts:
                leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{cl}"></span>'
                        f'<span class="legend-name">{nm}</span><span class="legend-pct">{max(v,0):.1f}%</span></div>')
            st.markdown(leg, unsafe_allow_html=True)
            if lost_b > 15:
                st.markdown(f'<div style="margin-top:8px;background:{C["amber_soft"]};border:1px solid #FEDF89;border-radius:10px;'
                            f'padding:9px 12px;font-size:11.5px;color:{C["amber_dark"]};font-weight:600;">'
                            f'⚠️ {lost_b:.1f}% من الظهور ضايع بسبب الميزانية — فرصة للزيادة.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r5r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Hourly Performance — أفضل أوقات الأداء</div>', unsafe_allow_html=True)
    df_hr = load_extra(str(d_from), str(d_to), ["hour_of_day", "day_of_week", "clicks", "conversions"])
    if selected_campaigns and not df_hr.empty and "campaign" in df_hr.columns:
        df_hr = df_hr[df_hr["campaign"].isin(selected_campaigns)]
    if df_hr.empty or "hour_of_day" not in df_hr.columns or "day_of_week" not in df_hr.columns:
        st.info("مفيش بيانات ساعات.")
    else:
        hm_metric = st.radio("المقياس", ["Clicks", "Spend", "Conversions"], horizontal=True,
                             key="hm_metric", label_visibility="collapsed")
        mcol = {"Clicks": "clicks", "Spend": "spend", "Conversions": "conversions"}[hm_metric]
        dh = df_hr.copy()
        dh["hour_of_day"] = pd.to_numeric(dh["hour_of_day"], errors="coerce")
        dh = dh.dropna(subset=["hour_of_day"])
        dh["hour_of_day"] = dh["hour_of_day"].astype(int)
        pivot = dh.groupby(["day_of_week", "hour_of_day"])[mcol].sum().reset_index()
        order = ["SATURDAY", "SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
        short = {"SATURDAY": "Sat", "SUNDAY": "Sun", "MONDAY": "Mon", "TUESDAY": "Tue",
                 "WEDNESDAY": "Wed", "THURSDAY": "Thu", "FRIDAY": "Fri"}
        pt = pivot.pivot(index="day_of_week", columns="hour_of_day", values=mcol).fillna(0)
        pt = pt.reindex([d for d in order if d in pt.index])
        fig = go.Figure(go.Heatmap(
            z=pt.values, x=[f"{h:02d}" for h in pt.columns], y=[short.get(d, d) for d in pt.index],
            colorscale=[[0, "#EEF2FF"], [0.5, "#93B4FD"], [1, C["indigo"]]],
            hovertemplate="%{y} %{x}:00<br>"+hm_metric+": %{z:,.0f}<extra></extra>",
            colorbar=dict(thickness=10, len=0.85, tickfont=dict(size=9)),
        ))
        fig.update_layout(**{k: v for k, v in PLOT.items() if k in ("paper_bgcolor", "plot_bgcolor", "font")},
                          height=250, margin=dict(l=6, r=6, t=6, b=6),
                          xaxis=dict(tickfont=dict(size=9), side="bottom"), yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        # best slot
        if not pivot.empty:
            top = pivot.sort_values(mcol, ascending=False).iloc[0]
            st.markdown(f'<div style="font-size:11.5px;color:{C["ink2"]};margin-top:4px;">'
                        f'🏆 أعلى {hm_metric}: <b>{short.get(top["day_of_week"], top["day_of_week"])} '
                        f'{int(top["hour_of_day"]):02d}:00</b> ({fmt_number(top[mcol])})</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 6 — KEYWORDS  +  TOP CAMPAIGNS
# ══════════════════════════════════════════════════════════
st.markdown(sec("🔑 Keywords & Campaigns"), unsafe_allow_html=True)
r6l, r6r = st.columns(2)

with r6l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Top Keywords</div>', unsafe_allow_html=True)
    df_kw = load_extra(str(d_from), str(d_to), ["keyword_text", "clicks", "conversions", "conversions_value"])
    if selected_campaigns and not df_kw.empty and "campaign" in df_kw.columns:
        df_kw = df_kw[df_kw["campaign"].isin(selected_campaigns)]
    if df_kw.empty or "keyword_text" not in df_kw.columns:
        st.info("مفيش بيانات كلمات مفتاحية (متاحة لحملات Search فقط).")
    else:
        g = df_kw.groupby("keyword_text", as_index=False).agg({
            "spend": "sum", "clicks": "sum", "conversions": "sum", "conversions_value": "sum"})
        g = g[(g["spend"] > 0) | (g["clicks"] > 0)].copy()
        g["roas"] = (g["conversions_value"] / g["spend"]).replace([float("inf")], 0).fillna(0)
        g["cpc"] = (g["spend"] / g["clicks"]).replace([float("inf")], 0).fillna(0)
        g = g.sort_values("spend", ascending=False)
        rows = []
        for _, r in g.head(15).iterrows():
            rr = r["roas"]
            badge = ('<span class="badge badge-green">قوي</span>' if rr >= 3 else
                     '<span class="badge badge-amber">متوسط</span>' if rr >= 1 else
                     '<span class="badge badge-red">ضعيف</span>')
            rows.append(
                f"<tr><td style='font-weight:600;max-width:190px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{r['keyword_text']}</td>"
                f"<td>{fmt_number(r['clicks'])}</td><td>{fmt_currency(r['spend'],2)}</td>"
                f"<td>{fmt_currency(r['cpc'],2)}</td><td>{r['conversions']:.1f}</td>"
                f"<td>{rr:.2f}x</td><td>{badge}</td></tr>")
        st.markdown(
            "<table class='styled-table'><thead><tr><th>Keyword</th><th>Clicks</th><th>Cost</th>"
            "<th>CPC</th><th>Conv.</th><th>ROAS</th><th></th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r6r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Top Campaigns</div>', unsafe_allow_html=True)
    gc = df.groupby(["campaign", "campaign_type"], as_index=False).agg({
        "spend": "sum", "clicks": "sum", "impressions": "sum",
        "conversions": "sum", "conversions_value": "sum"}) if "campaign_type" in df.columns else \
        df.groupby("campaign", as_index=False).agg({
            "spend": "sum", "clicks": "sum", "impressions": "sum",
            "conversions": "sum", "conversions_value": "sum"})
    gc = gc[gc["spend"] > 0].copy()
    gc["roas"] = (gc["conversions_value"] / gc["spend"]).replace([float("inf")], 0).fillna(0)
    gc["cpa"] = (gc["spend"] / gc["conversions"]).replace([float("inf")], 0).fillna(0)
    gc = gc.sort_values("spend", ascending=False)
    tbadge = {"SEARCH": "badge-blue", "PERFORMANCE_MAX": "badge-purple",
              "DEMAND_GEN": "badge-amber", "MULTI_CHANNEL": "badge-green"}
    tshort = {"SEARCH": "Search", "PERFORMANCE_MAX": "PMax", "DEMAND_GEN": "DemandGen", "MULTI_CHANNEL": "App"}
    rows = []
    for _, r in gc.head(15).iterrows():
        rr = r["roas"]
        tb = ""
        if "campaign_type" in gc.columns:
            t = str(r["campaign_type"])
            tb = f'<span class="badge {tbadge.get(t,"badge-blue")}">{tshort.get(t, t)}</span>'
        rows.append(
            f"<tr><td style='font-weight:600;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{r['campaign']}</td>"
            f"<td>{tb}</td><td>{fmt_currency(r['spend'])}</td>"
            f"<td>{r['conversions']:.1f}</td><td>{fmt_currency(r['conversions_value'])}</td>"
            f"<td>{rr:.2f}x</td><td>{fmt_currency(r['cpa'],2) if r['conversions']>0 else '—'}</td></tr>")
    st.markdown(
        "<table class='styled-table'><thead><tr><th>Campaign</th><th>Type</th><th>Cost</th>"
        "<th>Conv.</th><th>Revenue</th><th>ROAS</th><th>CPA</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 7 — DAILY PERFORMANCE TABLE
# ══════════════════════════════════════════════════════════
if not daily.empty:
    st.markdown(sec("📋 Performance by Day"), unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    tb = daily.sort_values("date", ascending=False).copy()
    tb["date"] = tb["date"].dt.strftime("%b %d, %Y")
    tb["ctr"] = (tb["clicks"] / tb["impressions"] * 100).replace([float("inf")], 0).fillna(0)
    tb["cpc"] = (tb["spend"] / tb["clicks"]).replace([float("inf")], 0).fillna(0)
    show = tb[["date", "spend", "impressions", "clicks", "ctr", "cpc", "conversions", "cpa", "conversions_value", "roas"]]
    st.dataframe(
        show, use_container_width=True, height=380, hide_index=True,
        column_config={
            "date": st.column_config.TextColumn("Date"),
            "spend": st.column_config.NumberColumn("Cost", format="$%,.2f"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%,d"),
            "clicks": st.column_config.NumberColumn("Clicks", format="%,d"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "cpc": st.column_config.NumberColumn("CPC", format="$%.2f"),
            "conversions": st.column_config.NumberColumn("Conv.", format="%.1f"),
            "cpa": st.column_config.NumberColumn("CPA", format="$%.2f"),
            "conversions_value": st.column_config.NumberColumn("Revenue", format="$%,.0f"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2fx"),
        },
    )
    buf = io.BytesIO()
    show.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("📥 Download CSV", buf.getvalue(), "google_ads_performance.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("💡 كل الأرقام مصدرها Google Ads مباشرة عبر Windsor.ai. الكلمات المفتاحية و Impression Share متاحة لحملات Search فقط.")
