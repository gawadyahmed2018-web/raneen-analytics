"""
Raneen GA4 — Decision Intelligence Center.
Source: Google Analytics 4 (Web + App) via Windsor.ai.

Built as an analyst's tool, not a chart gallery:
decision bar (quantified problems) · health scorecard · money map (RPS + index) ·
segmented funnel explorer · opportunity engine · product intelligence ·
landing-page quality · web-vs-app economics · anomaly radar · campaigns.
"""

import io
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from windsor import get_windsor_data, safe_num, fmt_currency, fmt_number, fmt_pct

st.set_page_config(page_title="Raneen GA4", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

C = {
    "green": "#16B364", "green_soft": "#DCFAE6", "green_dark": "#087443",
    "amber": "#F5A623", "amber_soft": "#FEF0C7", "amber_dark": "#B54708",
    "red": "#F04438", "red_soft": "#FEE4E2", "red_dark": "#B42318",
    "blue": "#2E90FA", "blue_soft": "#DBEAFE", "blue_dark": "#175CD3",
    "indigo": "#4F46E5", "indigo_soft": "#E0E7FF",
    "purple": "#7A5AF8", "purple_soft": "#EDE9FE", "purple_dark": "#6D28D9",
    "teal": "#14B8A6", "teal_soft": "#CCFBF1", "pink": "#EC4899", "orange": "#F97316",
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
.brand-logo {{ width:42px; height:42px; border-radius:11px; background:linear-gradient(135deg,{C['orange']},{C['amber']});
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
.kpi-split {{ display:flex; gap:8px; margin-top:8px; padding-top:7px; border-top:1px dashed {C['line']}; font-size:10.5px; }}
.kpi-web {{ color:{C['blue']}; font-weight:700; }}
.kpi-app {{ color:{C['purple']}; font-weight:700; }}

.sec {{ display:flex; align-items:center; gap:10px; margin:22px 0 12px; }}
.sec-t {{ font-size:16px; font-weight:750; color:{C['ink']}; letter-spacing:-.01em; }}
.sec-s {{ font-size:12px; color:{C['ink3']}; margin-left:auto; }}
.card {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:20px;
  box-shadow:0 1px 3px rgba(15,23,42,.04); height:100%; }}
.card-t {{ font-size:14px; font-weight:750; color:{C['ink']}; margin-bottom:10px; }}
.card-sub {{ font-size:11.5px; color:{C['ink3']}; font-weight:500; margin:-6px 0 12px; }}

/* decision bar */
.dec {{ display:flex; align-items:flex-start; gap:11px; padding:13px 16px; border-radius:14px;
  margin-bottom:9px; border:1px solid transparent; }}
.dec-ico {{ font-size:17px; line-height:1.4; }}
.dec-txt {{ font-size:13px; line-height:1.6; flex:1; }}
.dec-val {{ font-size:14px; font-weight:800; white-space:nowrap; }}
.dec-red {{ background:{C['red_soft']}; border-color:#FECDCA; color:{C['red_dark']}; }}
.dec-amber {{ background:{C['amber_soft']}; border-color:#FEDF89; color:{C['amber_dark']}; }}
.dec-green {{ background:{C['green_soft']}; border-color:#A6F4C5; color:{C['green_dark']}; }}
.dec-blue {{ background:{C['blue_soft']}; border-color:#B2DDFF; color:{C['blue_dark']}; }}

.idx {{ display:inline-block; font-size:10.5px; font-weight:800; padding:2px 8px; border-radius:100px; }}
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
.legend-row {{ display:flex; align-items:center; gap:8px; margin-bottom:8px; font-size:12.5px; }}
.legend-dot {{ width:9px; height:9px; border-radius:3px; }}
.legend-name {{ color:{C['ink2']}; font-weight:600; flex:1; }}
.legend-pct {{ color:{C['ink']}; font-weight:700; }}
.legend-val {{ color:{C['ink3']}; min-width:62px; text-align:right; }}

/* mini funnel bars for the segmented explorer */
.mf-name {{ font-size:12.5px; font-weight:700; color:{C['ink']}; margin-bottom:7px; }}
.mf-step {{ display:flex; align-items:center; gap:9px; margin-bottom:5px; }}
.mf-lbl {{ font-size:10.5px; color:{C['ink3']}; min-width:82px; }}
.mf-track {{ flex:1; height:16px; background:{C['line']}; border-radius:5px; overflow:hidden; }}
.mf-fill {{ height:100%; border-radius:5px; }}
.mf-val {{ font-size:10.5px; color:{C['ink2']}; min-width:74px; text-align:right; font-weight:600; }}
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
#  ANALYST HELPERS
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
    return (f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h+3}" preserveAspectRatio="none" style="display:block;">'
            f'<polygon points="0,{h} {line} {w},{h}" fill="{color}" opacity="0.08"/>'
            f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" fill="{color}"/></svg>')


def kpi(icon, name, value, unit, delta_pct, spark_vals, color, soft, sub="", is_bad_up=False, split=None):
    sp = spark(spark_vals, color) if spark_vals else ""
    delta_html = ""
    if delta_pct is not None:
        good = (delta_pct < 0) if is_bad_up else (delta_pct >= 0)
        dcol = C["green"] if good else C["red"]
        arrow = "▲" if delta_pct >= 0 else "▼"
        delta_html = f'<span class="kpi-delta" style="color:{dcol}">{arrow} {abs(delta_pct):.1f}%</span>'
    sub_html = f'<span class="kpi-sub2">{sub}</span>' if sub else '<span></span>'
    split_html = ""
    if split:
        split_html = (f'<div class="kpi-split"><span class="kpi-web">🌐 {split[0]}</span>'
                      f'<span style="color:{C["ink3"]}">·</span>'
                      f'<span class="kpi-app">📱 {split[1]}</span></div>')
    return (f'<div class="kpi">'
            f'<div class="kpi-name"><span class="kpi-ico" style="background:{soft};color:{color}">{icon}</span>{name}</div>'
            f'<div class="kpi-val">{value}<span class="kpi-unit">{unit}</span></div>'
            f'<div class="kpi-meta">{sub_html}{delta_html}</div>'
            f'{split_html}<div style="margin-top:8px">{sp}</div></div>')


def sec(title, sub=""):
    s = f'<span class="sec-s">{sub}</span>' if sub else ""
    return f'<div class="sec"><div class="sec-t">{title}</div>{s}</div>'


def pct_change(cur, prev):
    return 0.0 if prev == 0 else (cur - prev) / prev * 100


def idx_pill(index):
    """Performance index vs site average (100 = on par)."""
    if index >= 115:  bg, fg = C["green_soft"], C["green_dark"]
    elif index >= 85: bg, fg = C["blue_soft"], C["blue_dark"]
    elif index >= 60: bg, fg = C["amber_soft"], C["amber_dark"]
    else:             bg, fg = C["red_soft"], C["red_dark"]
    return f'<span class="idx" style="background:{bg};color:{fg}">{index:.0f}</span>'


def segment_stats(frame, dim):
    """Aggregate funnel metrics by a dimension and derive CVR, RPS and AOV."""
    if frame.empty or dim not in frame.columns:
        return pd.DataFrame()
    cols = [c for c in ["sessions", "active_users", "items_viewed", "add_to_carts",
                        "checkouts", "transactions", "purchase_revenue"] if c in frame.columns]
    g = frame.groupby(dim, as_index=False)[cols].sum()
    g = g[g.get("sessions", pd.Series(dtype=float)) > 0].copy()
    if g.empty:
        return g
    g["cvr"] = (g["transactions"] / g["sessions"] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    g["rps"] = (g["purchase_revenue"] / g["sessions"]).replace([np.inf, -np.inf], 0).fillna(0)
    g["aov"] = (g["purchase_revenue"] / g["transactions"]).replace([np.inf, -np.inf], 0).fillna(0)
    g[dim] = g[dim].astype(str)
    g = g[~g[dim].str.lower().isin(["(not set)", "nan", "none", ""])]
    return g.sort_values("purchase_revenue", ascending=False)


def opportunity(seg_sessions, seg_cvr, target_cvr, seg_aov):
    """Incremental revenue if a segment converted at the target rate."""
    if seg_cvr >= target_cvr or seg_sessions <= 0 or seg_aov <= 0:
        return 0.0
    extra_trans = seg_sessions * (target_cvr - seg_cvr) / 100
    return extra_trans * seg_aov


def funnel_steps(row):
    """Ordered funnel steps present in a segment row."""
    order = [("Sessions", "sessions"), ("Item Views", "items_viewed"),
             ("Add to Cart", "add_to_carts"), ("Checkout", "checkouts"),
             ("Purchase", "transactions")]
    return [(lbl, float(row[c])) for lbl, c in order if c in row.index and float(row[c]) > 0]


# ══════════════════════════════════════════════════════════
#  PERIOD
# ══════════════════════════════════════════════════════════
def preset_range(preset):
    today = date.today()
    m = {"last_7d": (today - timedelta(days=7), today - timedelta(days=1)),
         "last_14d": (today - timedelta(days=14), today - timedelta(days=1)),
         "last_30d": (today - timedelta(days=30), today - timedelta(days=1)),
         "last_90d": (today - timedelta(days=90), today - timedelta(days=1)),
         "this_month": (today.replace(day=1), today - timedelta(days=1)),
         "last_month": ((today.replace(day=1) - timedelta(days=1)).replace(day=1),
                        today.replace(day=1) - timedelta(days=1))}
    return m.get(preset, m["last_30d"])


def previous_range(dfrom, dto):
    a, b = pd.to_datetime(dfrom).date(), pd.to_datetime(dto).date()
    length = (b - a).days + 1
    prev_to = a - timedelta(days=1)
    return str(prev_to - timedelta(days=length - 1)), str(prev_to)


with st.sidebar:
    st.markdown("## 📊 Google Analytics 4")
    st.caption("Decision Intelligence — Web + App")
    st.markdown("---")
    date_preset = st.selectbox(
        "Date Range", ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month"],
        format_func=lambda x: {"last_7d": "Last 7 Days", "last_14d": "Last 14 Days",
                               "last_30d": "Last 30 Days", "last_90d": "Last 90 Days",
                               "this_month": "This Month", "last_month": "Last Month"}.get(x, x))
    _pf, _pt = preset_range(date_preset)
    st.markdown("**📅 نطاق مخصص**")
    _range = st.date_input("اختر الفترة", value=(_pf, _pt), max_value=date.today(),
                           format="YYYY-MM-DD", label_visibility="collapsed",
                           key=f"ga4_dr_{date_preset}")
    if isinstance(_range, (tuple, list)) and len(_range) == 2:
        d_from, d_to = _range
    elif isinstance(_range, (tuple, list)) and len(_range) == 1:
        d_from = d_to = _range[0]
    else:
        d_from = d_to = _range
    st.caption(f"الفترة: {d_from} → {d_to}")
    st.markdown("---")
    st.caption("💡 GA4 مباشرة — Raneen.com + Raneen Mobile APP")

prev_from, prev_to = previous_range(d_from, d_to)

FUNNEL_METRICS = ["sessions", "active_users", "items_viewed", "add_to_carts",
                  "checkouts", "transactions", "purchase_revenue"]
CORE_FIELDS = ["date"] + FUNNEL_METRICS + ["bounce_rate", "average_session_duration"]


def _clean(df, cols):
    if df.empty:
        return df
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    return df


@st.cache_data(ttl=300, show_spinner="Loading GA4 data...")
def load_core(dfrom, dto):
    return _clean(get_windsor_data(CORE_FIELDS, date_from=dfrom, date_to=dto, source="both", timeout=60),
                  FUNNEL_METRICS + ["bounce_rate", "average_session_duration"])


@st.cache_data(ttl=300, show_spinner=False)
def load_dim(dfrom, dto, dims, metrics=None, timeout=75):
    mets = list(metrics or FUNNEL_METRICS)
    return _clean(get_windsor_data(list(dims) + mets, date_from=dfrom, date_to=dto,
                                   source="both", timeout=timeout), mets)


df_all = load_core(str(d_from), str(d_to))
df_prev_all = load_core(prev_from, prev_to)

if df_all.empty:
    st.markdown('<div class="topbar"><div class="brand"><div class="brand-logo">📊</div>'
                '<div><div class="brand-t">Google Analytics 4 — Decision Center</div>'
                '<div class="brand-s">Customer behaviour & revenue intelligence</div></div></div></div>',
                unsafe_allow_html=True)
    st.warning("⚠️ لا توجد بيانات من GA4 في الفترة دي.")
    st.stop()


# ══════════════════════════════════════════════════════════
#  SCOPE
# ══════════════════════════════════════════════════════════
SCOPES = {"🔀 All (Web + App)": "both", "🌐 Web only": "web", "📱 App only": "app"}
scope_label = st.radio("النطاق", list(SCOPES.keys()), horizontal=True,
                       key="ga4_scope", label_visibility="collapsed")
scope = SCOPES[scope_label]


def apply_scope(frame):
    if frame.empty or scope == "both" or "source" not in frame.columns:
        return frame
    return frame[frame["source"] == scope]


df = apply_scope(df_all).copy()
df_prev = apply_scope(df_prev_all).copy()
if df.empty:
    st.info(f"مفيش بيانات لـ {scope_label}.")
    st.stop()


# ══════════════════════════════════════════════════════════
#  TOTALS & SITE BENCHMARKS
# ══════════════════════════════════════════════════════════
def tot(frame, col):
    return frame[col].sum() if (not frame.empty and col in frame.columns) else 0


def wavg(frame, col, weight="sessions"):
    if frame.empty or col not in frame.columns or weight not in frame.columns:
        return 0
    w = frame[weight].fillna(0)
    return 0 if w.sum() == 0 else (frame[col].fillna(0) * w).sum() / w.sum()


t_sessions = tot(df, "sessions");        t_users = tot(df, "active_users")
t_revenue = tot(df, "purchase_revenue"); t_trans = tot(df, "transactions")
t_atc = tot(df, "add_to_carts");         t_checkout = tot(df, "checkouts")
t_views = tot(df, "items_viewed")
t_bounce = wavg(df, "bounce_rate");      t_dur = wavg(df, "average_session_duration")

p_sessions = tot(df_prev, "sessions");   p_users = tot(df_prev, "active_users")
p_revenue = tot(df_prev, "purchase_revenue"); p_trans = tot(df_prev, "transactions")
p_bounce = wavg(df_prev, "bounce_rate")

# site-wide benchmarks — every segment is indexed against these
BM_CVR = (t_trans / t_sessions * 100) if t_sessions else 0
BM_RPS = (t_revenue / t_sessions) if t_sessions else 0
BM_AOV = (t_revenue / t_trans) if t_trans else 0
p_cvr = (p_trans / p_sessions * 100) if p_sessions else 0
p_aov = (p_revenue / p_trans) if p_trans else 0
engagement = (100 - t_bounce * 100) if t_bounce <= 1 else (100 - t_bounce)
p_engagement = (100 - p_bounce * 100) if p_bounce <= 1 else (100 - p_bounce)

web_rows = df_all[df_all["source"] == "web"] if "source" in df_all.columns else df_all.iloc[0:0]
app_rows = df_all[df_all["source"] == "app"] if "source" in df_all.columns else df_all.iloc[0:0]


def split_of(col, fmt=fmt_number):
    return (fmt(tot(web_rows, col)), fmt(tot(app_rows, col))) if scope == "both" else None


daily = pd.DataFrame()
if "date" in df.columns:
    dd = df.copy()
    dd["date"] = pd.to_datetime(dd["date"], errors="coerce")
    agg = {c: "sum" for c in FUNNEL_METRICS if c in dd.columns}
    daily = dd.dropna(subset=["date"]).groupby("date", as_index=False).agg(agg).sort_values("date")
    if {"transactions", "sessions"} <= set(daily.columns):
        daily["cvr"] = (daily["transactions"] / daily["sessions"] * 100).replace([np.inf], 0).fillna(0)
        daily["rps"] = (daily["purchase_revenue"] / daily["sessions"]).replace([np.inf], 0).fillna(0)


def dser(col):
    return daily[col].tolist() if (not daily.empty and col in daily.columns) else []


# shared breakdowns (cached; sliced client-side by scope)
def get_seg(dim, metrics=None, timeout=75):
    try:
        return apply_scope(load_dim(str(d_from), str(d_to), [dim], metrics, timeout))
    except Exception:
        return pd.DataFrame()


seg_channel = segment_stats(get_seg("session_default_channel_group"), "session_default_channel_group")
seg_device = segment_stats(get_seg("devicecategory"), "devicecategory")
seg_visitor = segment_stats(get_seg("new_vs_returning"), "new_vs_returning")


# ══════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-logo">📊</div>
    <div>
      <div class="brand-t">GA4 — Decision Intelligence <span class="live-dot">● Live</span></div>
      <div class="brand-s">Customer behaviour & revenue intelligence · Web + App</div>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
    <span class="chip">📅 {d_from} → {d_to}</span>
    <span class="chip">🔄 Compare: {prev_from} → {prev_to}</span>
    <span class="chip" style="color:{C['blue_dark']};background:{C['blue_soft']};border-color:#B2DDFF;">{scope_label}</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  DECISION BAR — problems, quantified in EGP
# ══════════════════════════════════════════════════════════
def build_decisions():
    out = []

    # 1) worst-converting segments vs the site benchmark
    for seg_df, dim, label in [(seg_device, "devicecategory", "جهاز"),
                               (seg_channel, "session_default_channel_group", "قناة"),
                               (seg_visitor, "new_vs_returning", "زائر")]:
        if seg_df.empty:
            continue
        cand = seg_df[seg_df["sessions"] >= seg_df["sessions"].sum() * 0.05]
        for _, r in cand.iterrows():
            gain = opportunity(r["sessions"], r["cvr"], BM_CVR, r["aov"] or BM_AOV)
            if gain > 0:
                out.append((gain, "red", "🔻",
                            f'<b>{r[dim]}</b> ({label}) بيحوّل <b>{r["cvr"]:.2f}%</b> مقابل '
                            f'<b>{BM_CVR:.2f}%</b> متوسط الموقع — لو وصل للمتوسط',
                            f"+{fmt_currency(gain)}"))

    # 2) biggest funnel leak overall
    stages = [("Item Views", t_views), ("Add to Cart", t_atc), ("Checkout", t_checkout), ("Purchase", t_trans)]
    stages = [(n, v) for n, v in stages if v > 0]
    if len(stages) >= 2:
        worst, worst_drop, worst_from = None, -1, 0
        for i in range(1, len(stages)):
            pn, pv = stages[i-1]; cn, cv = stages[i]
            drop = 100 - (cv / pv * 100 if pv else 0)
            if drop > worst_drop:
                worst_drop, worst, worst_from = drop, f"{pn} → {cn}", pv
        recovered = worst_from * 0.10 * (t_trans / max(t_checkout, 1)) * BM_AOV if worst_from else 0
        out.append((recovered, "amber", "🚰",
                    f'أكبر تسريب في الفانل عند <b>{worst}</b> ({worst_drop:.1f}%) — '
                    f'تحسينه 10 نقاط يقدّر بـ',
                    f"+{fmt_currency(recovered)}"))

    # 3) under-invested high-quality channel (high RPS, low traffic share)
    if not seg_channel.empty and BM_RPS > 0:
        ch = seg_channel.copy()
        ch["share"] = ch["sessions"] / ch["sessions"].sum() * 100
        star = ch[(ch["rps"] > BM_RPS * 1.15) & (ch["share"] < 20)]
        if not star.empty:
            r = star.sort_values("rps", ascending=False).iloc[0]
            out.append((0, "green", "💎",
                        f'<b>{r["session_default_channel_group"]}</b> أعلى جودة '
                        f'(<b>{fmt_currency(r["rps"],1)}</b>/جلسة مقابل {fmt_currency(BM_RPS,1)}) '
                        f'لكن نصيبه <b>{r["share"]:.1f}%</b> فقط من الترافيك — فرصة توسّع',
                        f'RPS {r["rps"]/BM_RPS*100:.0f}'))

    # 4) web vs app economics
    if scope == "both" and not web_rows.empty and not app_rows.empty:
        w_s, a_s = tot(web_rows, "sessions"), tot(app_rows, "sessions")
        w_c = (tot(web_rows, "transactions") / w_s * 100) if w_s else 0
        a_c = (tot(app_rows, "transactions") / a_s * 100) if a_s else 0
        w_aov = (tot(web_rows, "purchase_revenue") / max(tot(web_rows, "transactions"), 1))
        a_aov = (tot(app_rows, "purchase_revenue") / max(tot(app_rows, "transactions"), 1))
        if a_c < w_c:
            gain = opportunity(a_s, a_c, w_c, a_aov or BM_AOV)
            out.append((gain, "red", "📱",
                        f'<b>التطبيق</b> بيحوّل <b>{a_c:.2f}%</b> مقابل <b>{w_c:.2f}%</b> للويب — '
                        f'لو ساوى الويب', f"+{fmt_currency(gain)}"))
        elif w_c < a_c:
            gain = opportunity(w_s, w_c, a_c, w_aov or BM_AOV)
            out.append((gain, "red", "🌐",
                        f'<b>الويب</b> بيحوّل <b>{w_c:.2f}%</b> مقابل <b>{a_c:.2f}%</b> للتطبيق — '
                        f'لو ساوى التطبيق', f"+{fmt_currency(gain)}"))

    # 5) traffic / revenue trend
    d_rev = pct_change(t_revenue, p_revenue)
    out.append((0, "blue" if d_rev >= 0 else "amber", "📈" if d_rev >= 0 else "📉",
                f'الإيراد <b>{fmt_currency(t_revenue)}</b> ({d_rev:+.1f}%) من '
                f'<b>{fmt_number(t_trans)}</b> عملية · AOV {fmt_currency(BM_AOV,0)} · '
                f'RPS {fmt_currency(BM_RPS,1)}', f"{d_rev:+.1f}%"))

    out.sort(key=lambda x: -x[0])
    return out[:5]


st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-t">🎯 Decisions — أهم الفرص مقدّرة بالجنيه</div>', unsafe_allow_html=True)
st.markdown(f'<div class="card-sub">مرتبة حسب الأثر المالي · المقارنة بمتوسط الموقع '
            f'(CVR {BM_CVR:.2f}% · RPS {fmt_currency(BM_RPS,1)})</div>', unsafe_allow_html=True)
for _, kind, ico, txt, val in build_decisions():
    st.markdown(f'<div class="dec dec-{kind}"><span class="dec-ico">{ico}</span>'
                f'<span class="dec-txt">{txt}</span><span class="dec-val">{val}</span></div>',
                unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  SCORECARD
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.markdown(kpi("👥", "Users", fmt_number(t_users), "", pct_change(t_users, p_users),
                    dser("active_users"), C["blue"], C["blue_soft"], split=split_of("active_users")),
                unsafe_allow_html=True)
with k2:
    st.markdown(kpi("🔗", "Sessions", fmt_number(t_sessions), "", pct_change(t_sessions, p_sessions),
                    dser("sessions"), C["indigo"], C["indigo_soft"], split=split_of("sessions")),
                unsafe_allow_html=True)
with k3:
    st.markdown(kpi("💰", "Revenue", fmt_currency(t_revenue), "", pct_change(t_revenue, p_revenue),
                    dser("purchase_revenue"), C["green"], C["green_soft"],
                    split=split_of("purchase_revenue", fmt_currency)), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("🎯", "Conversion Rate", f"{BM_CVR:.2f}", "%", pct_change(BM_CVR, p_cvr),
                    dser("cvr"), C["purple"], C["purple_soft"],
                    sub=f"{fmt_number(t_trans)} trans"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi("💵", "Revenue / Session", fmt_currency(BM_RPS, 1), "",
                    pct_change(BM_RPS, (p_revenue/p_sessions) if p_sessions else 0), dser("rps"),
                    C["teal"], C["teal_soft"], sub="جودة الترافيك"), unsafe_allow_html=True)
with k6:
    st.markdown(kpi("🧾", "AOV", fmt_currency(BM_AOV, 0), "", pct_change(BM_AOV, p_aov), None,
                    C["orange"], C["amber_soft"], sub=f"Engagement {engagement:.0f}%"),
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  MONEY MAP — segment quality matrix
# ══════════════════════════════════════════════════════════
st.markdown(sec("🗺️ Money Map", "جودة كل شريحة مقارنة بمتوسط الموقع (Index 100 = المتوسط)"),
            unsafe_allow_html=True)


def money_table(seg_df, dim, title, top=8):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-t">{title}</div>', unsafe_allow_html=True)
    if seg_df.empty:
        st.info("مفيش بيانات.")
    else:
        tot_sess = seg_df["sessions"].sum()
        rows = []
        for _, r in seg_df.head(top).iterrows():
            share = r["sessions"] / tot_sess * 100 if tot_sess else 0
            idx = (r["rps"] / BM_RPS * 100) if BM_RPS else 0
            gain = opportunity(r["sessions"], r["cvr"], BM_CVR, r["aov"] or BM_AOV)
            gain_html = (f'<span style="color:{C["red"]};font-weight:700">+{fmt_currency(gain)}</span>'
                         if gain > 0 else f'<span style="color:{C["ink3"]}">—</span>')
            rows.append(f"<tr><td style='font-weight:600'>{r[dim]}</td>"
                        f"<td>{fmt_number(r['sessions'])}<br>"
                        f"<span style='font-size:10px;color:{C['ink3']}'>{share:.1f}%</span></td>"
                        f"<td>{r['cvr']:.2f}%</td>"
                        f"<td><b>{fmt_currency(r['rps'],1)}</b></td>"
                        f"<td>{fmt_currency(r['purchase_revenue'])}</td>"
                        f"<td>{idx_pill(idx)}</td><td>{gain_html}</td></tr>")
        st.markdown("<table class='styled-table'><thead><tr><th>Segment</th><th>Sessions</th>"
                    "<th>CVR</th><th>RPS</th><th>Revenue</th><th>Index</th><th>فرصة</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


mm1, mm2 = st.columns(2)
with mm1:
    money_table(seg_channel, "session_default_channel_group", "حسب القناة")
with mm2:
    money_table(seg_device, "devicecategory", "حسب الجهاز")
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
money_table(seg_visitor, "new_vs_returning", "جديد مقابل عائد")


# ══════════════════════════════════════════════════════════
#  SEGMENTED FUNNEL EXPLORER
# ══════════════════════════════════════════════════════════
st.markdown(sec("🔻 Funnel Explorer", "فين بالظبط بتخسر كل شريحة"), unsafe_allow_html=True)

DIMS = {"📡 القناة": ("session_default_channel_group", seg_channel),
        "📱 الجهاز": ("devicecategory", seg_device),
        "🔁 جديد / عائد": ("new_vs_returning", seg_visitor)}
if scope == "both":
    DIMS["🌐 ويب / تطبيق"] = ("source", segment_stats(df_all.assign(source=df_all["source"]), "source"))

dim_label = st.radio("قطّع حسب", list(DIMS.keys()), horizontal=True,
                     key="ga4_funnel_dim", label_visibility="collapsed")
dim_col, dim_df = DIMS[dim_label]

st.markdown('<div class="card">', unsafe_allow_html=True)
if dim_df.empty:
    st.info("مفيش بيانات للبُعد ده.")
else:
    show = dim_df.head(4)
    fcols = st.columns(len(show))
    step_colors = [C["blue"], C["indigo"], C["amber"], C["orange"], C["green"]]
    for col_st, (_, r) in zip(fcols, show.iterrows()):
        with col_st:
            steps = funnel_steps(r)
            if not steps:
                continue
            top_v = steps[0][1]
            html = f'<div class="mf-name">{r[dim_col]}</div>'
            for i, (lbl, val) in enumerate(steps):
                w = (val / top_v * 100) if top_v else 0
                html += (f'<div class="mf-step"><span class="mf-lbl">{lbl}</span>'
                         f'<div class="mf-track"><div class="mf-fill" '
                         f'style="width:{max(w,1.5)}%;background:{step_colors[i%len(step_colors)]}"></div></div>'
                         f'<span class="mf-val">{fmt_number(val)}</span></div>')
                if i < len(steps) - 1:
                    nxt = steps[i+1][1]
                    drop = 100 - (nxt / val * 100 if val else 0)
                    dc = C["green_dark"] if drop <= 40 else (C["amber_dark"] if drop <= 75 else C["red_dark"])
                    html += (f'<div style="text-align:right;font-size:10px;color:{dc};'
                             f'font-weight:700;margin:-2px 0 4px;">▼ {drop:.1f}%</div>')
            end_cvr = (steps[-1][1] / top_v * 100) if top_v else 0
            ecol = C["green"] if end_cvr >= BM_CVR else C["red"]
            html += (f'<div style="margin-top:8px;padding-top:8px;border-top:1px solid {C["line"]};'
                     f'display:flex;justify-content:space-between;font-size:11.5px;">'
                     f'<span style="color:{C["ink3"]}">CVR</span>'
                     f'<b style="color:{ecol}">{end_cvr:.2f}%</b></div>')
            st.markdown(html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  OPPORTUNITY ENGINE
# ══════════════════════════════════════════════════════════
st.markdown(sec("💡 Opportunity Engine", "لو كل شريحة وصلت لمتوسط الموقع"), unsafe_allow_html=True)

opps = []
for seg_df, dcol, dname in [(seg_channel, "session_default_channel_group", "قناة"),
                            (seg_device, "devicecategory", "جهاز"),
                            (seg_visitor, "new_vs_returning", "زائر")]:
    if seg_df.empty:
        continue
    for _, r in seg_df.iterrows():
        if r["sessions"] < seg_df["sessions"].sum() * 0.02:
            continue
        gain = opportunity(r["sessions"], r["cvr"], BM_CVR, r["aov"] or BM_AOV)
        if gain > 0:
            opps.append({"seg": f"{r[dcol]}", "type": dname, "sessions": r["sessions"],
                         "cvr": r["cvr"], "gap": BM_CVR - r["cvr"], "gain": gain})

st.markdown('<div class="card">', unsafe_allow_html=True)
if not opps:
    st.markdown(f'<div style="color:{C["green_dark"]};font-size:13px;font-weight:600;">'
                f'✅ كل الشرائح فوق أو عند متوسط الموقع.</div>', unsafe_allow_html=True)
else:
    opps.sort(key=lambda x: -x["gain"])
    total_gain = sum(o["gain"] for o in opps)
    st.markdown(f'<div class="card-sub">إجمالي الفرص المقدّرة: '
                f'<b style="color:{C["green_dark"]};font-size:14px;">{fmt_currency(total_gain)}</b> '
                f'({total_gain/t_revenue*100:.1f}% من الإيراد الحالي)</div>', unsafe_allow_html=True)
    mx = opps[0]["gain"]
    rows = ""
    for o in opps[:10]:
        w = o["gain"] / mx * 100 if mx else 0
        rows += (f'<div class="bar-row" style="margin-bottom:11px;">'
                 f'<div style="min-width:190px;">'
                 f'<div style="font-size:12.5px;font-weight:700;color:{C["ink"]}">{o["seg"]}</div>'
                 f'<div style="font-size:10.5px;color:{C["ink3"]}">{o["type"]} · '
                 f'{fmt_number(o["sessions"])} جلسة · CVR {o["cvr"]:.2f}% '
                 f'(فجوة {o["gap"]:.2f} نقطة)</div></div>'
                 f'<div style="flex:1;height:11px;background:{C["line"]};border-radius:100px;overflow:hidden;">'
                 f'<div style="width:{max(w,2)}%;height:100%;background:{C["green"]};border-radius:100px;"></div></div>'
                 f'<div style="min-width:96px;text-align:right;font-weight:800;color:{C["green_dark"]};'
                 f'font-size:13px;">+{fmt_currency(o["gain"])}</div></div>')
    st.markdown(rows, unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:11px;color:{C["ink3"]};margin-top:6px;">'
                f'الحساب: (جلسات الشريحة × فجوة التحويل) × متوسط قيمة الطلب للشريحة. '
                f'تقدير تقريبي للترتيب بالأولوية، مش وعد بإيراد.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  TRENDS
# ══════════════════════════════════════════════════════════
st.markdown(sec("📈 Trends"), unsafe_allow_html=True)
tr1, tr2 = st.columns([1.5, 1])
with tr1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Revenue vs Sessions · مع خط جودة الترافيك (RPS)</div>',
                unsafe_allow_html=True)
    if not daily.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=daily["date"], y=daily["sessions"], name="Sessions",
                             marker_color="rgba(46,144,250,.28)",
                             hovertemplate="Sessions: %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["purchase_revenue"], name="Revenue",
                                 mode="lines", line=dict(color=C["green"], width=3), yaxis="y2",
                                 hovertemplate="Revenue: %{y:,.0f}<extra></extra>"))
        _p = {k: v for k, v in PLOT.items() if k != "yaxis"}
        fig.update_layout(**_p, height=310, hovermode="x unified",
                          yaxis=dict(title="Sessions", gridcolor=C["line"], zeroline=False),
                          yaxis2=dict(title="Revenue", overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
with tr2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Conversion Rate — يومي مقابل المتوسط</div>', unsafe_allow_html=True)
    if not daily.empty and "cvr" in daily.columns:
        colors = [C["green"] if v >= BM_CVR else C["red"] for v in daily["cvr"]]
        fig = go.Figure(go.Bar(x=daily["date"], y=daily["cvr"], marker_color=colors,
                               hovertemplate="CVR: %{y:.2f}%<extra></extra>"))
        fig.add_hline(y=BM_CVR, line_dash="dash", line_color=C["ink3"],
                      annotation_text=f"متوسط {BM_CVR:.2f}%", annotation_position="top left")
        fig.update_layout(**PLOT, height=310)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  PRODUCT INTELLIGENCE — diagnose merchandising vs checkout
# ══════════════════════════════════════════════════════════
st.markdown(sec("🛍 Product Intelligence", "View→Cart يشخّص العرض · Cart→Buy يشخّص السعر/الشيك أوت"),
            unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
try:
    df_cat = get_seg("item_category", ["item_revenue", "items_purchased", "items_viewed",
                                       "items_added_to_cart", "item_price"], timeout=90)
    g = df_cat.groupby("item_category", as_index=False).agg(
        {"item_revenue": "sum", "items_purchased": "sum",
         "items_viewed": "sum", "items_added_to_cart": "sum", "item_price": "mean"})
    g["item_category"] = g["item_category"].astype(str)
    g = g[(g["item_revenue"] > 0) & (~g["item_category"].str.lower().isin(["(not set)", "nan", "none", ""]))]
    if g.empty:
        st.info("مفيش بيانات فئات.")
    else:
        g["v2c"] = (g["items_added_to_cart"] / g["items_viewed"] * 100).replace([np.inf], 0).fillna(0)
        g["c2p"] = (g["items_purchased"] / g["items_added_to_cart"] * 100).replace([np.inf], 0).fillna(0)
        avg_v2c, avg_c2p = g["v2c"].mean(), g["c2p"].mean()
        g = g.sort_values("item_revenue", ascending=False)
        rows = []
        for _, r in g.head(14).iterrows():
            # diagnosis: which stage is the weak one relative to the catalogue average
            if r["v2c"] < avg_v2c * 0.75:
                diag, dcls = "عرض / سعر معروض", "badge-amber"
            elif r["c2p"] < avg_c2p * 0.75:
                diag, dcls = "شحن / دفع / توفر", "badge-red"
            else:
                diag, dcls = "صحية", "badge-green"
            rows.append(f"<tr><td style='font-weight:600'>{r['item_category']}</td>"
                        f"<td>{fmt_currency(r['item_revenue'])}</td>"
                        f"<td>{fmt_number(r['items_viewed'])}</td>"
                        f"<td>{r['v2c']:.1f}%</td><td>{r['c2p']:.1f}%</td>"
                        f"<td>{fmt_number(r['items_purchased'])}</td>"
                        f"<td>{fmt_currency(r['item_price'],0)}</td>"
                        f"<td><span class='badge {dcls}'>{diag}</span></td></tr>")
        st.markdown(f'<div class="card-sub">متوسط الكتالوج: View→Cart {avg_v2c:.1f}% · '
                    f'Cart→Buy {avg_c2p:.1f}% — التشخيص مقارنة بالمتوسط</div>', unsafe_allow_html=True)
        st.markdown("<table class='styled-table'><thead><tr><th>Category</th><th>Revenue</th><th>Views</th>"
                    "<th>View→Cart</th><th>Cart→Buy</th><th>Sold</th><th>Avg Price</th>"
                    "<th>التشخيص</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
except Exception:
    st.info("مفيش بيانات فئات.")
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  LANDING PAGE QUALITY  +  WEB vs APP ECONOMICS
# ══════════════════════════════════════════════════════════
st.markdown(sec("🚪 Entry Quality & Platform Economics"), unsafe_allow_html=True)
lp_l, lp_r = st.columns([1.4, 1])

with lp_l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Landing Pages — ترافيك عالي + تحويل منخفض = نزيف</div>',
                unsafe_allow_html=True)
    try:
        df_pp = get_seg("page_path", ["sessions", "purchase_revenue", "transactions"], timeout=90)
        rich = not df_pp.empty and "purchase_revenue" in df_pp.columns
        if df_pp.empty:
            df_pp = get_seg("page_path", ["sessions"], timeout=90)
            rich = False
        agg = {"sessions": "sum"}
        if rich:
            agg.update({"purchase_revenue": "sum", "transactions": "sum"})
        g = df_pp.groupby("page_path", as_index=False).agg(agg)
        g = g[g["sessions"] > 0].sort_values("sessions", ascending=False)
        rows = []
        for _, r in g.head(12).iterrows():
            path = str(r["page_path"]); short = (path[:42] + "…") if len(path) > 44 else path
            if rich:
                cvr_p = (r["transactions"] / r["sessions"] * 100) if r["sessions"] else 0
                rps_p = (r["purchase_revenue"] / r["sessions"]) if r["sessions"] else 0
                idx = (rps_p / BM_RPS * 100) if BM_RPS else 0
                flag = ('<span class="badge badge-red">نزيف</span>'
                        if (idx < 60 and r["sessions"] > g["sessions"].median()) else "")
                rows.append(f"<tr><td style='font-weight:600' title='{path}'>{short}</td>"
                            f"<td>{fmt_number(r['sessions'])}</td><td>{cvr_p:.2f}%</td>"
                            f"<td>{fmt_currency(rps_p,1)}</td><td>{idx_pill(idx)}</td><td>{flag}</td></tr>")
            else:
                rows.append(f"<tr><td style='font-weight:600' title='{path}'>{short}</td>"
                            f"<td>{fmt_number(r['sessions'])}</td></tr>")
        head = ("<th>Page</th><th>Sessions</th><th>CVR</th><th>RPS</th><th>Index</th><th></th>"
                if rich else "<th>Page</th><th>Sessions</th>")
        st.markdown(f"<table class='styled-table'><thead><tr>{head}</tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    except Exception:
        st.info("مفيش بيانات صفحات.")
    st.markdown('</div>', unsafe_allow_html=True)

with lp_r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Web vs App — اقتصاديات المنصتين</div>', unsafe_allow_html=True)
    if web_rows.empty or app_rows.empty:
        st.info("محتاج بيانات المنصتين للمقارنة.")
    else:
        def econ(rows_):
            s = tot(rows_, "sessions"); tr = tot(rows_, "transactions"); rv = tot(rows_, "purchase_revenue")
            return {"sessions": s, "cvr": (tr/s*100) if s else 0, "rps": (rv/s) if s else 0,
                    "aov": (rv/tr) if tr else 0, "revenue": rv}
        W, A = econ(web_rows), econ(app_rows)
        for label, key, fmt in [("Sessions", "sessions", fmt_number), ("CVR %", "cvr", lambda v: f"{v:.2f}%"),
                                ("RPS", "rps", lambda v: fmt_currency(v, 1)),
                                ("AOV", "aov", lambda v: fmt_currency(v, 0)),
                                ("Revenue", "revenue", fmt_currency)]:
            wv, av = W[key], A[key]
            tot_v = (wv + av) or 1
            wpct = wv / tot_v * 100 if key in ("sessions", "revenue") else (wv / (wv + av) * 100 if (wv+av) else 50)
            better = C["blue"] if wv >= av else C["purple"]
            st.markdown(
                f'<div style="margin-bottom:11px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:4px;">'
                f'<span style="color:{C["ink2"]};font-weight:600;">{label}</span>'
                f'<span><b style="color:{C["blue"]}">{fmt(wv)}</b>'
                f'<span style="color:{C["ink3"]}"> · </span>'
                f'<b style="color:{C["purple"]}">{fmt(av)}</b></span></div>'
                f'<div style="display:flex;height:8px;border-radius:100px;overflow:hidden;">'
                f'<div style="width:{wpct}%;background:{C["blue"]}"></div>'
                f'<div style="width:{100-wpct}%;background:{C["purple"]}"></div></div></div>',
                unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:11px;color:{C["ink3"]};margin-top:4px;">'
                    f'<span style="color:{C["blue"]};font-weight:700">■</span> ويب &nbsp;'
                    f'<span style="color:{C["purple"]};font-weight:700">■</span> تطبيق</div>',
                    unsafe_allow_html=True)
        verdict = ("التطبيق أعلى جودة — يستاهل استثمار أكبر"
                   if A["rps"] > W["rps"] * 1.1 else
                   "الويب أعلى جودة — راجع تجربة التطبيق"
                   if W["rps"] > A["rps"] * 1.1 else "المنصتين متقاربتين في الجودة")
        st.markdown(f'<div style="margin-top:10px;padding:10px 12px;background:{C["bg"]};'
                    f'border:1px solid {C["line"]};border-radius:11px;font-size:12px;'
                    f'color:{C["ink2"]};font-weight:600;">💡 {verdict}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ANOMALY RADAR
# ══════════════════════════════════════════════════════════
st.markdown(sec("🚨 Anomaly Radar", "آخر يوم مقارنة بمتوسط الفترة ± انحرافين معياريين"),
            unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
if len(daily) < 5:
    st.info("محتاج 5 أيام على الأقل لكشف الشذوذ.")
else:
    checks = [("Sessions", "sessions", False), ("Revenue", "purchase_revenue", False),
              ("Conversion Rate", "cvr", False), ("Transactions", "transactions", False),
              ("Add to Cart", "add_to_carts", False)]
    found = []
    for label, col, _ in checks:
        if col not in daily.columns or len(daily[col]) < 5:
            continue
        hist = daily[col].iloc[:-1]
        last = daily[col].iloc[-1]
        mu, sd = hist.mean(), hist.std()
        if sd == 0 or pd.isna(sd):
            continue
        z = (last - mu) / sd
        if abs(z) >= 2:
            direction = "أعلى" if z > 0 else "أقل"
            kind = "green" if z > 0 else "red"
            ico = "📈" if z > 0 else "📉"
            fmt_v = fmt_currency if col == "purchase_revenue" else (
                (lambda v: f"{v:.2f}%") if col == "cvr" else fmt_number)
            found.append((abs(z), kind, ico,
                          f'<b>{label}</b> آخر يوم {direction} من المعتاد بشكل ملحوظ — '
                          f'{fmt_v(last)} مقابل متوسط {fmt_v(mu)}', f"{z:+.1f}σ"))
    if not found:
        st.markdown(f'<div style="color:{C["green_dark"]};font-size:13px;font-weight:600;">'
                    f'✅ مفيش شذوذ — كل المؤشرات في نطاقها الطبيعي.</div>', unsafe_allow_html=True)
    else:
        found.sort(key=lambda x: -x[0])
        for _, kind, ico, txt, val in found:
            st.markdown(f'<div class="dec dec-{kind}"><span class="dec-ico">{ico}</span>'
                        f'<span class="dec-txt">{txt}</span><span class="dec-val">{val}</span></div>',
                        unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  CAMPAIGNS  +  PRODUCTS BY CAMPAIGN
# ══════════════════════════════════════════════════════════
st.markdown(sec("📣 Campaigns → Products", "أي حملة بتبيع إيه فعلاً"), unsafe_allow_html=True)
CAMP_SRC = {"📘 Meta": "session_manual_campaign_name", "🔵 Google Ads": "session_google_ads_campaign_name"}
camp_choice = st.radio("مصدر الحملات", list(CAMP_SRC.keys()), horizontal=True,
                       key="ga4_camp_src", label_visibility="collapsed")
camp_field = CAMP_SRC[camp_choice]

cmp_l, cmp_r = st.columns([1.3, 1])
camp_list = []
with cmp_l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Campaigns — مرتبة بجودة الترافيك (RPS)</div>', unsafe_allow_html=True)
    try:
        gc = segment_stats(get_seg(camp_field, timeout=90), camp_field)
        camp_list = gc[camp_field].tolist()
        if gc.empty:
            st.info("مفيش بيانات حملات.")
        else:
            gc = gc.sort_values("rps", ascending=False)
            rows = []
            for _, r in gc.head(12).iterrows():
                nm = str(r[camp_field]); short = (nm[:34] + "…") if len(nm) > 36 else nm
                idx = (r["rps"] / BM_RPS * 100) if BM_RPS else 0
                rows.append(f"<tr><td style='font-weight:600' title='{nm}'>{short}</td>"
                            f"<td>{fmt_number(r['sessions'])}</td><td>{r['cvr']:.2f}%</td>"
                            f"<td><b>{fmt_currency(r['rps'],1)}</b></td>"
                            f"<td>{fmt_currency(r['purchase_revenue'])}</td>"
                            f"<td>{idx_pill(idx)}</td></tr>")
            st.markdown("<table class='styled-table'><thead><tr><th>Campaign</th><th>Sessions</th>"
                        "<th>CVR</th><th>RPS</th><th>Revenue</th><th>Index</th></tr></thead>"
                        f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    except Exception:
        st.info("مفيش بيانات حملات.")
    st.markdown('</div>', unsafe_allow_html=True)

with cmp_r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Products by Campaign</div>', unsafe_allow_html=True)
    if not camp_list:
        st.info("اختر مصدر حملات فيه بيانات.")
    else:
        sel_camp = st.selectbox("الكامبين", camp_list, key="ga4_prod_camp")
        try:
            df_pr = get_seg(camp_field, None, timeout=90)
            df_pr = apply_scope(load_dim(str(d_from), str(d_to), [camp_field, "item_name"],
                                         ["item_revenue", "items_purchased"], timeout=95))
            df_pr = df_pr[df_pr[camp_field].astype(str) == sel_camp]
            gp = df_pr.groupby("item_name", as_index=False).agg(
                {"item_revenue": "sum", "items_purchased": "sum"})
            gp = gp[gp["item_revenue"] > 0].sort_values("item_revenue", ascending=False)
            if gp.empty:
                st.info("مفيش منتجات للكامبين ده.")
            else:
                st.markdown(f'<div style="display:flex;gap:18px;margin-bottom:10px;">'
                            f'<div><div style="font-size:10.5px;color:{C["ink3"]};font-weight:600;">REVENUE</div>'
                            f'<div style="font-size:19px;font-weight:800;color:{C["green"]};">'
                            f'{fmt_currency(gp["item_revenue"].sum())}</div></div>'
                            f'<div><div style="font-size:10.5px;color:{C["ink3"]};font-weight:600;">PRODUCTS</div>'
                            f'<div style="font-size:19px;font-weight:800;color:{C["blue"]};">'
                            f'{fmt_number(len(gp))}</div></div></div>', unsafe_allow_html=True)
                rows = []
                for _, r in gp.head(10).iterrows():
                    nm = str(r["item_name"]); short = (nm[:32] + "…") if len(nm) > 34 else nm
                    rows.append(f"<tr><td style='font-weight:600' title='{nm}'>{short}</td>"
                                f"<td>{fmt_currency(r['item_revenue'])}</td>"
                                f"<td>{fmt_number(r['items_purchased'])}</td></tr>")
                st.markdown("<table class='styled-table'><thead><tr><th>Product</th><th>Revenue</th>"
                            "<th>Qty</th></tr></thead>"
                            f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        except Exception:
            st.info("مفيش بيانات منتجات.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  DAILY TABLE
# ══════════════════════════════════════════════════════════
if not daily.empty:
    st.markdown(sec("📋 Daily Performance"), unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    tb = daily.sort_values("date", ascending=False).copy()
    tb["date"] = tb["date"].dt.strftime("%b %d, %Y")
    tb["aov"] = (tb["purchase_revenue"] / tb["transactions"]).replace([np.inf], 0).fillna(0)
    cols_show = [c for c in ["date", "active_users", "sessions", "items_viewed", "add_to_carts",
                             "checkouts", "transactions", "cvr", "purchase_revenue", "rps", "aov"]
                 if c in tb.columns]
    st.dataframe(tb[cols_show], use_container_width=True, height=380, hide_index=True,
        column_config={
            "date": st.column_config.TextColumn("Date"),
            "active_users": st.column_config.NumberColumn("Users", format="%,d"),
            "sessions": st.column_config.NumberColumn("Sessions", format="%,d"),
            "items_viewed": st.column_config.NumberColumn("Item Views", format="%,d"),
            "add_to_carts": st.column_config.NumberColumn("Add to Cart", format="%,d"),
            "checkouts": st.column_config.NumberColumn("Checkouts", format="%,d"),
            "transactions": st.column_config.NumberColumn("Trans.", format="%,d"),
            "cvr": st.column_config.NumberColumn("CVR", format="%.2f%%"),
            "purchase_revenue": st.column_config.NumberColumn("Revenue", format="%,.0f"),
            "rps": st.column_config.NumberColumn("RPS", format="%.1f"),
            "aov": st.column_config.NumberColumn("AOV", format="%,.0f")})
    buf = io.BytesIO()
    tb[cols_show].to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("📥 Download CSV", buf.getvalue(), "ga4_performance.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("💡 GA4 عبر Windsor.ai — Raneen.com (Web) + Raneen Mobile APP. "
           "تقديرات الفرص إرشادية للترتيب بالأولوية.")
