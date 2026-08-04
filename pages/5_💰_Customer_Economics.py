"""
Raneen — Customer Economics (Executive Dashboard).

Three KPIs only:
  1) CAC  = Marketing Spend ÷ New Customers
  2) LTV  = Total GMV ÷ Unique Customers
  3) LTV:CAC Ratio = LTV ÷ CAC

Sources
  • Marketing Spend  → Meta (facebook) + Google Ads connectors  (field: spend)
  • GMV              → GA4 purchase_revenue
  • New Customers    → GA4 first_time_purchasers  (fallback: 'new' segment)
  • Unique Customers → GA4 total_purchasers       (fallback: transactions)

Filters: Date · Channel · Platform (Web/App) · Customer Segment.
Style mirrors the Executive Summary page (light theme, soft KPI cards).
"""

from datetime import date, timedelta

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from windsor import get_windsor_data, safe_num, fmt_currency, fmt_number, fmt_pct
from sheets_connector import load_sales_sheet

st.set_page_config(page_title="Raneen · Customer Economics", page_icon="💰",
                   layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════
#  DESIGN TOKENS  (matched to the other pages)
# ══════════════════════════════════════════════════════════
C = {
    "green": "#16B364", "green_soft": "#DCFAE6", "green_dark": "#087443",
    "amber": "#F5A623", "amber_soft": "#FEF0C7", "amber_dark": "#B54708",
    "red": "#F04438", "red_soft": "#FEE4E2", "red_dark": "#B42318",
    "blue": "#3B82F6", "blue_soft": "#DBEAFE", "blue_dark": "#1D4ED8",
    "purple": "#8B5CF6", "purple_soft": "#EDE9FE", "purple_dark": "#6D28D9",
    "teal": "#14B8A6", "pink": "#EC4899", "orange": "#F97316",
    "ink": "#0F172A", "ink2": "#475569", "ink3": "#94A3B8",
    "line": "#E9EDF2", "bg": "#F4F6FA", "card": "#FFFFFF",
}
STATUS = {"green": (C["green"], C["green_soft"], "Above Target"),
          "amber": (C["amber"], C["amber_soft"], "Close to Target"),
          "red":   (C["red"],   C["red_soft"],   "Below Target")}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family:'Inter','IBM Plex Sans Arabic',sans-serif; }}
#MainMenu, footer {{ visibility:hidden; }}
section[data-testid="stHeader"] {{ background:rgba(0,0,0,0); }}
.stApp {{ background:{C['bg']}; }}
.block-container {{ padding:1rem 1.6rem 2.6rem; max-width:1620px; }}
section[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid {C['line']}; }}
section[data-testid="stSidebar"] label {{ color:{C['ink2']} !important; font-size:12px; font-weight:600; }}

.topbar {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:16px 22px;
  margin-bottom:14px; display:flex; align-items:center; justify-content:space-between; gap:16px;
  flex-wrap:wrap; box-shadow:0 1px 3px rgba(15,23,42,.04); }}
.brand-t {{ font-size:21px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; }}
.brand-s {{ font-size:12.5px; color:{C['ink3']}; margin-top:2px; }}
.chip {{ background:{C['bg']}; border:1px solid {C['line']}; border-radius:11px; padding:8px 14px;
  font-size:12.5px; color:{C['ink2']}; font-weight:600; display:inline-flex; align-items:center; gap:7px; }}

.card {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:16px; padding:18px;
  box-shadow:0 1px 3px rgba(15,23,42,.04); height:100%; }}
.card-t {{ font-size:14px; font-weight:750; color:{C['ink']}; margin-bottom:2px; }}
.card-sub {{ font-size:11px; color:{C['ink3']}; font-weight:500; margin-bottom:11px; }}

.kpi {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:16px; padding:18px 18px 16px;
  box-shadow:0 1px 3px rgba(15,23,42,.04); border-left:5px solid {C['line']}; height:100%; }}
.kpi-top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }}
.kpi-name {{ font-size:12.5px; color:{C['ink2']}; font-weight:700; display:flex; align-items:center; gap:6px; }}
.kpi-ico {{ width:28px; height:28px; border-radius:9px; display:flex; align-items:center; justify-content:center; font-size:14px; }}
.kpi-pill {{ font-size:10.5px; font-weight:800; padding:3px 10px; border-radius:100px; }}
.kpi-val {{ font-size:30px; font-weight:900; color:{C['ink']}; letter-spacing:-.02em; line-height:1.04; }}
.kpi-unit {{ font-size:13px; font-weight:700; color:{C['ink3']}; margin-left:4px; }}
.kpi-row {{ display:flex; align-items:center; justify-content:space-between; margin-top:10px;
  padding-top:9px; border-top:1px dashed {C['line']}; font-size:11.5px; }}
.kpi-lbl {{ color:{C['ink3']}; font-weight:600; }}
.kpi-num {{ color:{C['ink']}; font-weight:800; }}
.kpi-delta {{ font-weight:800; display:inline-flex; align-items:center; gap:3px; }}
.kpi-tgt {{ margin-top:8px; font-size:11px; color:{C['ink3']}; font-weight:600; }}
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=C["ink2"], size=11),
    margin=dict(l=6, r=6, t=10, b=6),
    xaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False, tickfont=dict(size=10)),
    yaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False, tickfont=dict(size=10)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    hoverlabel=dict(bgcolor="white", bordercolor=C["line"], font_size=11),
)

ALL_CH = "كل القنوات"
ALL_SEG = "كل الشرائح"


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def _num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def pick(df, *cands):
    for c in cands:
        if c in df.columns:
            return c
    return None


def prev_range(d_from, d_to):
    length = (d_to - d_from).days + 1
    p_to = d_from - timedelta(days=1)
    p_from = p_to - timedelta(days=length - 1)
    return p_from, p_to


def safe_div(a, b):
    a, b = safe_num(a), safe_num(b)
    return a / b if b else 0.0


def spark_svg(vals, color, w=118, h=32):
    vals = [v for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    n = len(vals)
    pts = " ".join(f"{i/(n-1)*w:.1f},{h-(v-mn)/rng*(h-4)-2:.1f}" for i, v in enumerate(vals))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/></svg>')


# ══════════════════════════════════════════════════════════
#  DATA FETCH
# ══════════════════════════════════════════════════════════
GA_DIMS = ["date", "session_default_channel_group", "new_vs_returning"]
GA_METS = ["first_time_purchasers", "total_purchasers", "purchase_revenue", "transactions"]
GA_MET_FALLBACK = ["purchase_revenue", "transactions", "active_users"]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ga(dfrom, dto):
    """GA4 daily rows split by channel · segment · source(web/app)."""
    df = get_windsor_data(GA_DIMS + GA_METS, date_from=str(dfrom), date_to=str(dto),
                          source="both", timeout=90)
    if not df.empty and "purchase_revenue" in df.columns:
        return _num(df, GA_METS)
    # fallback — drop the purchaser metrics that some connectors don't expose
    df = get_windsor_data(GA_DIMS + GA_MET_FALLBACK, date_from=str(dfrom), date_to=str(dto),
                          source="both", timeout=90)
    return _num(df, GA_MET_FALLBACK) if not df.empty else pd.DataFrame()


# Marketing spend comes from the finance sheet (same source as the Executive
# Summary), NOT the live ad connectors — so numbers reconcile with finance.
SHEET_TOTAL = "Total Spending"
SHEET_CH_COLS = ["Facebook Spending", "Google Spending", "TikTok Spending",
                 "SMS Spending", "Criteo Spending", "Coupons", "Extra Spending"]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_spend(dfrom, dto):
    """Daily marketing spend from the sales sheet, sliced to the window.

    Returns df[date, total, <channel columns that exist>].
    """
    df = load_sales_sheet()
    if df.empty or "Date" not in df.columns:
        return pd.DataFrame(columns=["date", "total"])
    d = df.copy()
    d["date"] = pd.to_datetime(d["Date"], errors="coerce")
    d = d.dropna(subset=["date"])
    d = d[(d["date"].dt.date >= dfrom) & (d["date"].dt.date <= dto)]
    keep = [SHEET_TOTAL] + [c for c in SHEET_CH_COLS if c in d.columns]
    keep = [c for c in keep if c in d.columns]
    if SHEET_TOTAL not in keep:
        return pd.DataFrame(columns=["date", "total"])
    for c in keep:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    out = d.groupby("date", as_index=False)[keep].sum().rename(columns={SHEET_TOTAL: "total"})
    return out


# ══════════════════════════════════════════════════════════
#  SIDEBAR — FILTERS & TARGETS
# ══════════════════════════════════════════════════════════
st.sidebar.markdown("### 🎛️ الفلاتر")
today = date.today()
default_from = today - timedelta(days=30)
dr = st.sidebar.date_input("الفترة الزمنية", (default_from, today - timedelta(days=1)),
                           max_value=today, key="ce_dates")
if isinstance(dr, (tuple, list)) and len(dr) == 2:
    d_from, d_to = dr
else:
    d_from = d_to = dr if not isinstance(dr, (tuple, list)) else dr[0]
p_from, p_to = prev_range(d_from, d_to)

# fetch current + previous
ga_cur = fetch_ga(d_from, d_to)
ga_prev = fetch_ga(p_from, p_to)
sp_cur = fetch_spend(d_from, d_to)
sp_prev = fetch_spend(p_from, p_to)

if ga_cur.empty:
    st.markdown('<div class="topbar"><div><div class="brand-t">Customer Economics</div>'
                '<div class="brand-s">CAC · LTV · LTV:CAC</div></div></div>', unsafe_allow_html=True)
    st.warning("⚠️ لا توجد بيانات GA4 في الفترة دي.")
    st.stop()

# resolve column names once
CH_COL = pick(ga_cur, "session_default_channel_group")
SEG_COL = pick(ga_cur, "new_vs_returning")
NEW_COL = pick(ga_cur, "first_time_purchasers")
UNIQ_COL = pick(ga_cur, "total_purchasers", "transactions")
REV_COL = pick(ga_cur, "purchase_revenue", "total_revenue")

# channel filter options
if CH_COL:
    ch_vals = (ga_cur[CH_COL].astype(str)
               .replace({"(not set)": None, "nan": None, "None": None}).dropna().unique().tolist())
    ch_options = [ALL_CH] + sorted([c for c in ch_vals if c.strip()])
else:
    ch_options = [ALL_CH]
sel_ch = st.sidebar.selectbox("القناة", ch_options, key="ce_ch")

# platform filter
plat_map = {"🔀 الكل": "both", "🌐 Web": "web", "📱 App": "app"}
sel_plat_lbl = st.sidebar.selectbox("المنصة", list(plat_map.keys()), key="ce_plat")
sel_plat = plat_map[sel_plat_lbl]

# segment filter
if SEG_COL:
    seg_vals = ga_cur[SEG_COL].astype(str).replace({"nan": None, "None": None}).dropna().unique().tolist()
    seg_options = [ALL_SEG] + sorted([s for s in seg_vals if s.strip()])
else:
    seg_options = [ALL_SEG]
sel_seg = st.sidebar.selectbox("شريحة العملاء", seg_options, key="ce_seg")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 التارجت")
cac_target = st.sidebar.number_input("CAC Target (ج)", min_value=0.0, value=200.0, step=10.0)
ltv_target = st.sidebar.number_input("LTV Target (ج)", min_value=0.0, value=1200.0, step=50.0)
ratio_target = st.sidebar.number_input("LTV:CAC Target", min_value=0.0, value=3.0, step=0.5)


# ══════════════════════════════════════════════════════════
#  AGGREGATION PIPELINE
# ══════════════════════════════════════════════════════════
def _apply_common(df):
    """Filter by platform + channel (shared by every metric)."""
    d = df.copy()
    if sel_plat != "both" and "source" in d.columns:
        d = d[d["source"] == sel_plat]
    if sel_ch != ALL_CH and CH_COL:
        d = d[d[CH_COL].astype(str) == sel_ch]
    return d


def _new_customers(df):
    """New customers = first-time purchasers (acquisition is inherently 'new')."""
    d = _apply_common(df)
    if NEW_COL:
        return d.groupby(d["date"])[NEW_COL].sum()
    # fallback: purchasers within the 'new' segment
    if SEG_COL and UNIQ_COL:
        d = d[d[SEG_COL].astype(str).str.lower().str.startswith("new")]
        return d.groupby(d["date"])[UNIQ_COL].sum()
    return pd.Series(dtype=float)


def _ltv_base(df):
    """Unique customers + GMV for the LTV side — segment filter applies here."""
    d = _apply_common(df)
    if sel_seg != ALL_SEG and SEG_COL:
        d = d[d[SEG_COL].astype(str) == sel_seg]
    uniq = d.groupby(d["date"])[UNIQ_COL].sum() if UNIQ_COL else pd.Series(dtype=float)
    gmv = d.groupby(d["date"])[REV_COL].sum() if REV_COL else pd.Series(dtype=float)
    return uniq, gmv


def _spend_series(sp):
    """Daily spend from the sheet, mapped to the selected channel."""
    if sp.empty:
        return pd.Series(dtype=float)
    s = sp.set_index("date")
    if sel_ch == ALL_CH:
        return s["total"] if "total" in s.columns else pd.Series(0.0, index=s.index)
    cl = sel_ch.lower()
    if any(k in cl for k in ("social", "facebook", "meta", "instagram")):
        cols = ["Facebook Spending", "TikTok Spending"]      # paid social = Meta + TikTok
    elif any(k in cl for k in ("search", "shopping", "display", "video", "pmax",
                               "performance max", "cross-network", "google")):
        cols = ["Google Spending"]
    elif any(k in cl for k in ("email", "sms")):
        cols = ["SMS Spending"]
    else:
        return pd.Series(0.0, index=s.index)  # organic/direct/referral → no ad spend
    cols = [c for c in cols if c in s.columns]
    if not cols:
        return pd.Series(0.0, index=s.index)
    return s[cols].sum(axis=1)


def build_daily(ga, sp):
    new = _new_customers(ga).rename("new_customers")
    uniq, gmv = _ltv_base(ga)
    uniq = uniq.rename("uniq_customers")
    gmv = gmv.rename("gmv")
    spend = _spend_series(sp).rename("spend")
    # normalise all indexes to datetime
    def _dt(s):
        s.index = pd.to_datetime(s.index, errors="coerce")
        return s.groupby(level=0).sum()
    frame = pd.concat([_dt(new), _dt(uniq), _dt(gmv), _dt(spend)], axis=1).fillna(0)
    frame = frame.sort_index()
    frame["cac"] = frame.apply(lambda r: safe_div(r["spend"], r["new_customers"]), axis=1)
    frame["ltv"] = frame.apply(lambda r: safe_div(r["gmv"], r["uniq_customers"]), axis=1)
    frame["ratio"] = frame.apply(lambda r: safe_div(r["ltv"], r["cac"]), axis=1)
    return frame


daily = build_daily(ga_cur, sp_cur)
daily_prev = build_daily(ga_prev, sp_prev)


def totals(frame):
    spend = frame["spend"].sum()
    new = frame["new_customers"].sum()
    uniq = frame["uniq_customers"].sum()
    gmv = frame["gmv"].sum()
    cac = safe_div(spend, new)
    ltv = safe_div(gmv, uniq)
    ratio = safe_div(ltv, cac)
    return dict(spend=spend, new=new, uniq=uniq, gmv=gmv, cac=cac, ltv=ltv, ratio=ratio)


cur = totals(daily)
prv = totals(daily_prev)


# ══════════════════════════════════════════════════════════
#  STATUS LOGIC
# ══════════════════════════════════════════════════════════
def status_cac(v):
    if v <= 0:
        return "amber"
    if v <= cac_target:
        return "green"
    if v <= cac_target * 1.15:
        return "amber"
    return "red"


def status_ltv(v):
    if v >= ltv_target:
        return "green"
    if v >= ltv_target * 0.85:
        return "amber"
    return "red"


def status_ratio(v):
    if v < 1:
        return "red"
    if v <= 3:
        return "amber"
    return "green"


# ══════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════
notes = []
if sel_plat != "both":
    notes.append("الإنفاق مجمّع (Web/App مش منفصلين في مصدر الإنفاق)")
st.markdown(f"""
<div class="topbar">
  <div>
    <div class="brand-t">💰 Customer Economics</div>
    <div class="brand-s">CAC · LTV · LTV:CAC — {d_from} → {d_to}</div>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <span class="chip">📅 {(d_to - d_from).days + 1} يوم</span>
    <span class="chip">🔎 {sel_ch}</span>
    <span class="chip">{sel_plat_lbl}</span>
    <span class="chip">👥 {sel_seg}</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  KPI CARDS
# ══════════════════════════════════════════════════════════
def kpi_card(icon, name, cur_val, prev_val, unit, target_str, status_key,
             spark_vals, color, soft, lower_is_better=False, value_str=None):
    abs_ch = cur_val - prev_val
    pct_ch = safe_div(abs_ch, abs(prev_val)) * 100 if prev_val else 0.0
    up = abs_ch >= 0
    good = (not up) if lower_is_better else up
    dcol = C["green"] if good else C["red"]
    arrow = "↑" if up else "↓"
    scol, ssoft, slabel = STATUS[status_key]
    val_display = value_str if value_str is not None else f"{cur_val:,.1f}"
    prev_display = f"{prev_val:,.1f}" if unit != "" else f"{prev_val:,.2f}"
    sp = spark_svg(spark_vals, scol)
    return f"""
<div class="kpi" style="border-left-color:{scol};">
  <div class="kpi-top">
    <div class="kpi-name"><span class="kpi-ico" style="background:{soft};color:{color}">{icon}</span>{name}</div>
    <span class="kpi-pill" style="background:{ssoft};color:{scol};">{slabel}</span>
  </div>
  <div class="kpi-val">{val_display}<span class="kpi-unit">{unit}</span></div>
  <div class="kpi-row">
    <span class="kpi-lbl">الفترة السابقة</span>
    <span class="kpi-num">{prev_display}{(' '+unit) if unit else ''}</span>
  </div>
  <div class="kpi-row" style="border-top:none;padding-top:2px;margin-top:2px;">
    <span class="kpi-lbl">التغير</span>
    <span class="kpi-delta" style="color:{dcol};">{arrow} {abs(abs_ch):,.1f} &nbsp;({abs(pct_ch):.1f}%)</span>
  </div>
  <div class="kpi-tgt">🎯 Target: {target_str}</div>
  <div style="margin-top:6px">{sp}</div>
</div>"""


k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(kpi_card(
        "🎯", "Customer Acquisition Cost", cur["cac"], prv["cac"], "ج",
        f"≤ {fmt_number(cac_target)} ج", status_cac(cur["cac"]),
        daily["cac"].tolist(), C["red"], C["red_soft"],
        lower_is_better=True, value_str=f"{cur['cac']:,.1f}"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card(
        "💎", "Customer Lifetime Value", cur["ltv"], prv["ltv"], "ج",
        f"≥ {fmt_number(ltv_target)} ج", status_ltv(cur["ltv"]),
        daily["ltv"].tolist(), C["green"], C["green_soft"],
        lower_is_better=False, value_str=f"{cur['ltv']:,.1f}"), unsafe_allow_html=True)
with k3:
    rk = status_ratio(cur["ratio"])
    band = {"red": "🔴 Critical (<1)", "amber": "🟡 Needs Improvement (1–3)", "green": "🟢 Healthy (>3)"}[rk]
    st.markdown(kpi_card(
        "⚖️", "LTV : CAC Ratio", cur["ratio"], prv["ratio"], "",
        f"≥ {ratio_target:.1f}×  ·  {band}", rk,
        daily["ratio"].tolist(), C["purple"], C["purple_soft"],
        lower_is_better=False, value_str=f"{cur['ratio']:,.2f}×"), unsafe_allow_html=True)

if notes:
    st.caption("ℹ️ " + " · ".join(notes))


# ══════════════════════════════════════════════════════════
#  TREND PREP  (daily, or weekly if the range is long)
# ══════════════════════════════════════════════════════════
def resample_trend(frame):
    if frame.empty:
        return frame
    rule = "W" if (d_to - d_from).days > 45 else "D"
    agg = frame[["spend", "new_customers", "uniq_customers", "gmv"]].resample(rule).sum()
    agg["cac"] = agg.apply(lambda r: safe_div(r["spend"], r["new_customers"]), axis=1)
    agg["ltv"] = agg.apply(lambda r: safe_div(r["gmv"], r["uniq_customers"]), axis=1)
    agg["ratio"] = agg.apply(lambda r: safe_div(r["ltv"], r["cac"]), axis=1)
    return agg


tr = resample_trend(daily)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
cc1, cc2 = st.columns(2)

# ── Chart 1: LTV vs CAC trend ──
with cc1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">LTV vs CAC Trend</div>'
                '<div class="card-sub">القيمة مقابل تكلفة الاكتساب عبر الزمن (ج)</div>',
                unsafe_allow_html=True)
    if tr.empty:
        st.info("مفيش بيانات كفاية.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tr.index, y=tr["ltv"], name="LTV", mode="lines+markers",
                                 line=dict(color=C["green"], width=2.5),
                                 hovertemplate="LTV: %{y:,.0f} ج<extra></extra>"))
        fig.add_trace(go.Scatter(x=tr.index, y=tr["cac"], name="CAC", mode="lines+markers",
                                 line=dict(color=C["red"], width=2.5),
                                 hovertemplate="CAC: %{y:,.0f} ج<extra></extra>"))
        fig.update_layout(**PLOT, height=320)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Chart 2: LTV:CAC ratio trend with benchmark bands ──
with cc2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">LTV:CAC Ratio Trend</div>'
                '<div class="card-sub">🔴 &lt;1 · 🟡 1–3 · 🟢 &gt;3</div>',
                unsafe_allow_html=True)
    if tr.empty:
        st.info("مفيش بيانات كفاية.")
    else:
        ymax = max(4, float(np.nanmax(tr["ratio"].replace(0, np.nan))) * 1.15 if tr["ratio"].max() else 4)
        fig = go.Figure()
        # benchmark bands
        fig.add_hrect(y0=0, y1=1, fillcolor=C["red"], opacity=0.06, line_width=0)
        fig.add_hrect(y0=1, y1=3, fillcolor=C["amber"], opacity=0.07, line_width=0)
        fig.add_hrect(y0=3, y1=ymax, fillcolor=C["green"], opacity=0.06, line_width=0)
        for y in (1, 3):
            fig.add_hline(y=y, line_dash="dash", line_color=C["ink3"], line_width=1)
        fig.add_trace(go.Scatter(x=tr.index, y=tr["ratio"], name="LTV:CAC", mode="lines+markers",
                                 line=dict(color=C["purple"], width=2.8),
                                 hovertemplate="%{y:.2f}×<extra></extra>"))
        _p = {k: v for k, v in PLOT.items() if k != "yaxis"}
        fig.update_layout(**_p, height=320,
                          yaxis=dict(range=[0, ymax], gridcolor=C["line"], zeroline=False,
                                     tickfont=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── Chart 3: Marketing Spend vs New Customers (combo) ──
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-t">Marketing Spend vs New Customers</div>'
            '<div class="card-sub">الإنفاق (أعمدة) مقابل العملاء الجدد (خط)</div>',
            unsafe_allow_html=True)
if tr.empty:
    st.info("مفيش بيانات كفاية.")
else:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tr.index, y=tr["spend"], name="Marketing Spend",
                         marker_color="rgba(240,68,56,.65)",
                         hovertemplate="Spend: %{y:,.0f} ج<extra></extra>"))
    fig.add_trace(go.Scatter(x=tr.index, y=tr["new_customers"], name="New Customers",
                             mode="lines+markers", yaxis="y2",
                             line=dict(color=C["blue"], width=2.8),
                             hovertemplate="New: %{y:,.0f}<extra></extra>"))
    _p = {k: v for k, v in PLOT.items() if k != "yaxis"}
    fig.update_layout(**_p, height=340, barmode="group",
                      yaxis=dict(title="Spend (ج)", gridcolor=C["line"], zeroline=False,
                                 tickfont=dict(size=10)),
                      yaxis2=dict(title="New Customers", overlaying="y", side="right",
                                  showgrid=False, zeroline=False, tickfont=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ── diagnostics (raw components so numbers can be sanity-checked) ──
with st.expander("🔧 تشخيص الأرقام — Debug"):
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**الفترة الحالية**")
        st.write({
            "Marketing Spend (ج)": round(cur["spend"], 1),
            "New Customers": int(cur["new"]),
            "Unique Customers": int(cur["uniq"]),
            "GMV (ج)": round(cur["gmv"], 1),
            "CAC = Spend ÷ New": round(cur["cac"], 2),
            "LTV = GMV ÷ Unique": round(cur["ltv"], 1),
            "LTV:CAC": round(cur["ratio"], 2),
        })
    with dc2:
        st.markdown("**الإنفاق من الشيت**")
        brk = {"Total (ج)": round(float(sp_cur["total"].sum()), 1) if not sp_cur.empty else 0}
        for c in ("Facebook Spending", "Google Spending", "TikTok Spending", "SMS Spending"):
            if not sp_cur.empty and c in sp_cur.columns:
                brk[c] = round(float(sp_cur[c].sum()), 1)
        st.write(brk)
        se = st.session_state.get("_sheet_errors", [])
        if se:
            st.caption("⚠️ Sheet: " + str(se[-1])[:160])
        if sp_cur.empty or sp_cur["total"].sum() == 0:
            st.error("الإنفاق = صفر من الشيت. اتأكد إن SALES_SHEET_CSV_URL مضبوط "
                     "وإن الفترة فيها صفوف في الشيت.")

# ── data-source footnote ──
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
st.caption(
    "المصادر: الإنفاق من شيت المبيعات («Total Spending» — نفس مصدر الـ Executive Summary) · "
    f"GMV والعملاء من GA4 (GMV=«{REV_COL or '—'}», عملاء جدد=«{NEW_COL or 'مشتق من شريحة New'}», "
    f"عملاء فريدين=«{UNIQ_COL or '—'}»). فلتر القناة يربط الإنفاق: Social→Facebook+TikTok، "
    "Search/Shopping→Google، Email→SMS، والقنوات العضوية إنفاقها = صفر. "
    "فلتر المنصة (Web/App) والشريحة بيأثروا على جانب GA4 بس (الإنفاق مجمّع)."
)
