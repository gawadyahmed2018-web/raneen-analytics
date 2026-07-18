"""
Raneen GA4 — Command Center.
Source: Google Analytics 4 (Web + App) via Windsor.ai.

One long page with three scopes: All · Web only · App only.
Sections: AI summary, KPI grid, customer journey funnel, revenue vs users,
traffic sources, landing pages, top events, devices, geography, hourly heatmap,
category performance, campaigns, and products by campaign.
"""

import io
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from windsor import get_windsor_data, safe_num, fmt_currency, fmt_number, fmt_pct

st.set_page_config(page_title="Raneen GA4", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════
#  DESIGN TOKENS  (shared system across the hub)
# ══════════════════════════════════════════════════════════
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

.sec {{ display:flex; align-items:center; gap:10px; margin:20px 0 12px; }}
.sec-t {{ font-size:16px; font-weight:750; color:{C['ink']}; letter-spacing:-.01em; }}
.sec-s {{ font-size:12px; color:{C['ink3']}; margin-left:auto; }}

.card {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:20px;
  box-shadow:0 1px 3px rgba(15,23,42,.04); height:100%; }}
.card-t {{ font-size:14px; font-weight:750; color:{C['ink']}; margin-bottom:10px; }}

.ai-row {{ display:flex; align-items:flex-start; gap:9px; padding:8px 0; font-size:13px; color:{C['ink2']}; line-height:1.6; }}
.ai-row b {{ color:{C['ink']}; }}
.ai-ico {{ font-size:14px; }}

/* funnel */
.fn-wrap {{ display:flex; align-items:flex-start; justify-content:space-between; gap:4px; }}
.fn-step {{ flex:1; text-align:center; }}
.fn-circle {{ width:52px; height:52px; border-radius:16px; margin:0 auto 9px; display:flex;
  align-items:center; justify-content:center; font-size:22px; }}
.fn-label {{ font-size:11.5px; color:{C['ink2']}; font-weight:600; }}
.fn-value {{ font-size:19px; font-weight:800; color:{C['ink']}; margin-top:3px; letter-spacing:-.02em; }}
.fn-pct {{ font-size:11px; color:{C['ink3']}; margin-top:2px; }}
.fn-arrow {{ align-self:center; color:{C['ink3']}; font-size:16px; padding:0 2px; margin-top:-28px; }}
.fn-drop {{ display:inline-block; font-size:10.5px; font-weight:700; padding:3px 9px; border-radius:100px; margin-top:8px; }}

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
.legend-val {{ color:{C['ink3']}; min-width:60px; text-align:right; }}
.bar-row {{ display:flex; align-items:center; gap:10px; margin-bottom:9px; }}
.bar-name {{ font-size:12px; color:{C['ink2']}; min-width:120px; font-weight:600;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bar-track {{ flex:1; height:9px; background:{C['line']}; border-radius:100px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:100px; }}
.bar-val {{ font-size:12px; color:{C['ink']}; min-width:70px; text-align:right; font-weight:700; }}
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


def kpi(icon, name, value, unit, delta_pct, spark_vals, color, soft,
        sub="", is_bad_up=False, split=None):
    """split = (web_value, app_value) rendered as a small footer when scope is All."""
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
    return (
        f'<div class="kpi">'
        f'<div class="kpi-name"><span class="kpi-ico" style="background:{soft};color:{color}">{icon}</span>{name}</div>'
        f'<div class="kpi-val">{value}<span class="kpi-unit">{unit}</span></div>'
        f'<div class="kpi-meta">{sub_html}{delta_html}</div>'
        f'{split_html}<div style="margin-top:8px">{sp}</div></div>'
    )


def sec(title, sub=""):
    s = f'<span class="sec-s">{sub}</span>' if sub else ""
    return f'<div class="sec"><div class="sec-t">{title}</div>{s}</div>'


def pct_change(cur, prev):
    if prev == 0:
        return 0.0
    return (cur - prev) / prev * 100


# ══════════════════════════════════════════════════════════
#  SIDEBAR — period + custom range
# ══════════════════════════════════════════════════════════
def preset_range(preset):
    today = date.today()
    m = {
        "last_7d":  (today - timedelta(days=7),  today - timedelta(days=1)),
        "last_14d": (today - timedelta(days=14), today - timedelta(days=1)),
        "last_30d": (today - timedelta(days=30), today - timedelta(days=1)),
        "last_90d": (today - timedelta(days=90), today - timedelta(days=1)),
        "this_month": (today.replace(day=1), today - timedelta(days=1)),
        "last_month": ((today.replace(day=1) - timedelta(days=1)).replace(day=1),
                       today.replace(day=1) - timedelta(days=1)),
    }
    return m.get(preset, m["last_30d"])


def previous_range(dfrom, dto):
    a, b = pd.to_datetime(dfrom).date(), pd.to_datetime(dto).date()
    length = (b - a).days + 1
    prev_to = a - timedelta(days=1)
    return str(prev_to - timedelta(days=length - 1)), str(prev_to)


with st.sidebar:
    st.markdown("## 📊 Google Analytics 4")
    st.caption("Web + App — عبر Windsor.ai")
    st.markdown("---")
    date_preset = st.selectbox(
        "Date Range",
        ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month"],
        format_func=lambda x: {
            "last_7d": "Last 7 Days", "last_14d": "Last 14 Days", "last_30d": "Last 30 Days",
            "last_90d": "Last 90 Days", "this_month": "This Month", "last_month": "Last Month",
        }.get(x, x),
    )
    _pf, _pt = preset_range(date_preset)
    st.markdown("**📅 نطاق مخصص**")
    _range = st.date_input("اختر الفترة", value=(_pf, _pt), max_value=date.today(),
                           format="YYYY-MM-DD", label_visibility="collapsed",
                           key=f"ga4_dr_{date_preset}")
    if isinstance(_range, (tuple, list)) and len(_range) == 2:
        d_from, d_to = _range[0], _range[1]
    elif isinstance(_range, (tuple, list)) and len(_range) == 1:
        d_from = d_to = _range[0]
    else:
        d_from = d_to = _range
    st.caption(f"الفترة: {d_from} → {d_to}")
    st.markdown("---")
    st.caption("💡 المصدر: GA4 مباشرة (Raneen.com + Raneen Mobile APP)")

prev_from, prev_to = previous_range(d_from, d_to)


# ══════════════════════════════════════════════════════════
#  CORE DATA  (one merged request per account)
# ══════════════════════════════════════════════════════════
CORE_FIELDS = ["date", "sessions", "active_users", "purchase_revenue", "transactions",
               "add_to_carts", "checkouts", "items_viewed", "bounce_rate",
               "average_session_duration"]

NUMERIC = ["sessions", "active_users", "purchase_revenue", "transactions",
           "add_to_carts", "checkouts", "items_viewed", "bounce_rate",
           "average_session_duration"]


def _clean(df, cols=None):
    if df.empty:
        return df
    for c in (cols or NUMERIC):
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    return df


@st.cache_data(ttl=300, show_spinner="Loading GA4 data...")
def load_core(dfrom, dto):
    return _clean(get_windsor_data(CORE_FIELDS, date_from=dfrom, date_to=dto, source="both", timeout=60))


@st.cache_data(ttl=300, show_spinner=False)
def load_dim(dfrom, dto, dims, metrics, timeout=60):
    """Fetch one breakdown (dimension + metrics) for both accounts."""
    return _clean(get_windsor_data(list(dims) + list(metrics),
                                   date_from=dfrom, date_to=dto, source="both", timeout=timeout),
                  cols=metrics)


df_all = load_core(str(d_from), str(d_to))
df_prev_all = load_core(prev_from, prev_to)

if df_all.empty:
    st.markdown('<div class="topbar"><div class="brand"><div class="brand-logo">📊</div>'
                '<div><div class="brand-t">Google Analytics 4 — Command Center</div>'
                '<div class="brand-s">Customer behavior & website performance</div></div></div></div>',
                unsafe_allow_html=True)
    st.warning("⚠️ لا توجد بيانات من GA4 في الفترة دي. تأكد من الاتصال على Windsor.ai.")
    st.stop()


# ══════════════════════════════════════════════════════════
#  SCOPE TABS — All · Web only · App only
# ══════════════════════════════════════════════════════════
SCOPES = {"🔀 All (Web + App)": "both", "🌐 Web only": "web", "📱 App only": "app"}
scope_label = st.radio("النطاق", list(SCOPES.keys()), horizontal=True,
                       key="ga4_scope", label_visibility="collapsed")
scope = SCOPES[scope_label]


def apply_scope(df):
    if df.empty or scope == "both" or "source" not in df.columns:
        return df
    return df[df["source"] == scope]


df = apply_scope(df_all).copy()
df_prev = apply_scope(df_prev_all).copy()

if df.empty:
    st.info(f"مفيش بيانات لـ {scope_label} في الفترة دي.")
    st.stop()


# ══════════════════════════════════════════════════════════
#  TOTALS
# ══════════════════════════════════════════════════════════
def tot(frame, col):
    return frame[col].sum() if (not frame.empty and col in frame.columns) else 0


def wavg(frame, col, weight="sessions"):
    """Session-weighted average — the correct way to combine rates."""
    if frame.empty or col not in frame.columns or weight not in frame.columns:
        return 0
    w = frame[weight].fillna(0)
    if w.sum() == 0:
        return 0
    return (frame[col].fillna(0) * w).sum() / w.sum()


t_sessions = tot(df, "sessions");     t_users = tot(df, "active_users")
t_revenue = tot(df, "purchase_revenue"); t_trans = tot(df, "transactions")
t_atc = tot(df, "add_to_carts");      t_checkout = tot(df, "checkouts")
t_views = tot(df, "items_viewed")
t_bounce = wavg(df, "bounce_rate");   t_dur = wavg(df, "average_session_duration")

p_sessions = tot(df_prev, "sessions"); p_users = tot(df_prev, "active_users")
p_revenue = tot(df_prev, "purchase_revenue"); p_trans = tot(df_prev, "transactions")
p_bounce = wavg(df_prev, "bounce_rate")

cvr = (t_trans / t_sessions * 100) if t_sessions else 0
p_cvr = (p_trans / p_sessions * 100) if p_sessions else 0
aov = (t_revenue / t_trans) if t_trans else 0
p_aov = (p_revenue / p_trans) if p_trans else 0
rps = (t_revenue / t_sessions) if t_sessions else 0
engagement = (100 - t_bounce * 100) if t_bounce <= 1 else (100 - t_bounce)
p_engagement = (100 - p_bounce * 100) if p_bounce <= 1 else (100 - p_bounce)

# web / app split (for the All view)
web_rows = df_all[df_all["source"] == "web"] if "source" in df_all.columns else df_all.iloc[0:0]
app_rows = df_all[df_all["source"] == "app"] if "source" in df_all.columns else df_all.iloc[0:0]


def split_of(col, fmt=fmt_number):
    return (fmt(tot(web_rows, col)), fmt(tot(app_rows, col))) if scope == "both" else None


# daily series
daily = pd.DataFrame()
if "date" in df.columns:
    dd = df.copy()
    dd["date"] = pd.to_datetime(dd["date"], errors="coerce")
    agg = {c: "sum" for c in ["sessions", "active_users", "purchase_revenue", "transactions",
                              "add_to_carts", "checkouts", "items_viewed"] if c in dd.columns}
    daily = dd.dropna(subset=["date"]).groupby("date", as_index=False).agg(agg).sort_values("date")
    if "transactions" in daily.columns and "sessions" in daily.columns:
        daily["cvr"] = (daily["transactions"] / daily["sessions"] * 100).replace([float("inf")], 0).fillna(0)


def dser(col):
    return daily[col].tolist() if (not daily.empty and col in daily.columns) else []


# ══════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-logo">📊</div>
    <div>
      <div class="brand-t">Google Analytics 4 — Command Center <span class="live-dot">● Live</span></div>
      <div class="brand-s">Customer behavior intelligence & site/app performance</div>
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
#  AI EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-t">✨ AI Executive Summary</div>', unsafe_allow_html=True)

_ins = []
d_sess = pct_change(t_sessions, p_sessions)
_ins.append(("📈" if d_sess >= 0 else "📉",
             f'Traffic {"increased" if d_sess>=0 else "decreased"} by <b>{abs(d_sess):.1f}%</b> vs the previous period '
             f'({fmt_number(t_sessions)} sessions).'))
d_cvr = pct_change(cvr, p_cvr)
_ins.append(("🎯" if d_cvr >= 0 else "⚠️",
             f'Conversion rate is <b>{cvr:.2f}%</b>, {"up" if d_cvr>=0 else "down"} <b>{abs(d_cvr):.1f}%</b>.'))
d_rev = pct_change(t_revenue, p_revenue)
_ins.append(("💰", f'Revenue <b>{fmt_currency(t_revenue)}</b> ({d_rev:+.1f}%) from <b>{fmt_number(t_trans)}</b> transactions · AOV {fmt_currency(aov,0)}.'))

# biggest funnel leak
_stages = [("View Item", t_views), ("Add to Cart", t_atc), ("Checkout", t_checkout), ("Purchase", t_trans)]
_stages = [(n, v) for n, v in _stages if v > 0]
if len(_stages) >= 2:
    worst, worst_drop = None, -1
    for i in range(1, len(_stages)):
        pn, pv = _stages[i-1]; cn, cv = _stages[i]
        drop = 100 - (cv / pv * 100 if pv else 0)
        if drop > worst_drop:
            worst_drop, worst = drop, f"{pn} → {cn}"
    _ins.append(("🔻", f'Biggest funnel leak is <b>{worst}</b> — losing <b>{worst_drop:.1f}%</b> of users at that step.'))

# web vs app (only meaningful in All)
if scope == "both" and not web_rows.empty and not app_rows.empty:
    w_cvr = (tot(web_rows,"transactions")/tot(web_rows,"sessions")*100) if tot(web_rows,"sessions") else 0
    a_cvr = (tot(app_rows,"transactions")/tot(app_rows,"sessions")*100) if tot(app_rows,"sessions") else 0
    better, worse = ("Web", "App") if w_cvr >= a_cvr else ("App", "Web")
    _ins.append(("📱", f'<b>{better}</b> converts better ({max(w_cvr,a_cvr):.2f}% vs {min(w_cvr,a_cvr):.2f}%) — review the {worse} experience.'))

_c1, _c2 = st.columns(2)
for i, (ico, txt) in enumerate(_ins):
    with (_c1 if i % 2 == 0 else _c2):
        st.markdown(f'<div class="ai-row"><span class="ai-ico">{ico}</span><span>{txt}</span></div>',
                    unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  KPI GRID
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.markdown(kpi("👥", "Users", fmt_number(t_users), "", pct_change(t_users, p_users),
                    dser("active_users"), C["blue"], C["blue_soft"],
                    split=split_of("active_users")), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("🔗", "Sessions", fmt_number(t_sessions), "", d_sess,
                    dser("sessions"), C["indigo"], C["indigo_soft"],
                    split=split_of("sessions")), unsafe_allow_html=True)
with k3:
    st.markdown(kpi("💰", "Revenue", fmt_currency(t_revenue), "", pct_change(t_revenue, p_revenue),
                    dser("purchase_revenue"), C["green"], C["green_soft"],
                    split=split_of("purchase_revenue", fmt_currency)), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("🛍", "Transactions", fmt_number(t_trans), "", pct_change(t_trans, p_trans),
                    dser("transactions"), C["orange"], C["amber_soft"],
                    sub=f"AOV {fmt_currency(aov,0)}",
                    split=split_of("transactions")), unsafe_allow_html=True)
with k5:
    st.markdown(kpi("🎯", "Conversion Rate", f"{cvr:.2f}", "%", d_cvr, dser("cvr"),
                    C["purple"], C["purple_soft"], sub="Trans ÷ Sessions"), unsafe_allow_html=True)
with k6:
    st.markdown(kpi("💚", "Engagement Rate", f"{engagement:.1f}", "%",
                    pct_change(engagement, p_engagement), None, C["teal"], C["teal_soft"],
                    sub=f"Avg {t_dur:.0f}s / session"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  CUSTOMER JOURNEY FUNNEL
# ══════════════════════════════════════════════════════════
st.markdown(sec("🔻 Customer Journey", "من الزيارة للشراء — نسبة التسريب في كل خطوة"), unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)

steps = [
    ("👥", "Users", t_users, C["blue"], C["blue_soft"]),
    ("👁", "View Item", t_views, C["indigo"], C["indigo_soft"]),
    ("🛒", "Add to Cart", t_atc, C["amber"], C["amber_soft"]),
    ("💳", "Begin Checkout", t_checkout, C["orange"], "#FFEDD5"),
    ("✅", "Purchase", t_trans, C["green"], C["green_soft"]),
]
steps = [s for s in steps if s[2] > 0]

if len(steps) >= 2:
    top = steps[0][2]
    cols = st.columns(len(steps) * 2 - 1)
    for i, (ico, label, val, col, soft) in enumerate(steps):
        with cols[i * 2]:
            share = (val / top * 100) if top else 0
            st.markdown(
                f'<div class="fn-step">'
                f'<div class="fn-circle" style="background:{soft};color:{col}">{ico}</div>'
                f'<div class="fn-label">{label}</div>'
                f'<div class="fn-value">{fmt_number(val)}</div>'
                f'<div class="fn-pct">{share:.1f}%</div></div>',
                unsafe_allow_html=True)
        if i < len(steps) - 1:
            nxt = steps[i + 1][2]
            conv = (nxt / val * 100) if val else 0
            drop = 100 - conv
            dcol, dsoft = ((C["green_dark"], C["green_soft"]) if drop <= 40 else
                           (C["amber_dark"], C["amber_soft"]) if drop <= 70 else
                           (C["red_dark"], C["red_soft"]))
            with cols[i * 2 + 1]:
                st.markdown(
                    f'<div style="text-align:center;margin-top:14px;">'
                    f'<div style="color:{C["ink3"]};font-size:18px;">→</div>'
                    f'<span class="fn-drop" style="background:{dsoft};color:{dcol}">▼ {drop:.1f}%</span></div>',
                    unsafe_allow_html=True)
    overall = (t_trans / t_users * 100) if t_users else 0
    st.markdown(
        f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid {C["line"]};'
        f'display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-size:12.5px;color:{C["ink2"]};font-weight:600;">Overall Conversion (Users → Purchase)</span>'
        f'<span style="font-size:16px;color:{C["purple"]};font-weight:800;">{overall:.2f}%</span></div>',
        unsafe_allow_html=True)
else:
    st.info("مفيش بيانات كافية لرسم رحلة العميل.")
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW — REVENUE vs USERS  +  TRAFFIC SOURCES
# ══════════════════════════════════════════════════════════
st.markdown(sec("📈 Trends & Acquisition"), unsafe_allow_html=True)
r1l, r1r = st.columns([1.5, 1])

with r1l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Revenue vs Users</div>', unsafe_allow_html=True)
    if not daily.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["active_users"], name="Users",
                                 mode="lines+markers", line=dict(color=C["blue"], width=2.5),
                                 marker=dict(size=4), hovertemplate="Users: %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=daily["date"], y=daily["purchase_revenue"], name="Revenue",
                                 mode="lines+markers", line=dict(color=C["green"], width=2.5),
                                 marker=dict(size=4), yaxis="y2",
                                 hovertemplate="Revenue: %{y:,.0f}<extra></extra>"))
        _p = {k: v for k, v in PLOT.items() if k != "yaxis"}
        fig.update_layout(**_p, height=320, hovermode="x unified",
                          yaxis=dict(title="Users", gridcolor=C["line"], zeroline=False),
                          yaxis2=dict(title="Revenue", overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r1r:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Traffic Sources</div>', unsafe_allow_html=True)
    try:
        df_ch = apply_scope(load_dim(str(d_from), str(d_to), ["session_default_channel_group"],
                                     ["sessions", "purchase_revenue", "transactions"]))
        g = df_ch.groupby("session_default_channel_group", as_index=False).agg(
            {"sessions": "sum", "purchase_revenue": "sum", "transactions": "sum"})
        g = g[g["sessions"] > 0].sort_values("sessions", ascending=False)
        palette = [C["blue"], C["green"], C["purple"], C["amber"], C["pink"], C["teal"], C["orange"], C["ink3"]]
        fig = go.Figure(go.Pie(labels=g["session_default_channel_group"], values=g["sessions"], hole=0.66,
                               marker=dict(colors=palette[:len(g)], line=dict(color="#fff", width=2)),
                               textinfo="none", sort=False,
                               hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=180,
                          margin=dict(l=0, r=0, t=0, b=0),
                          annotations=[dict(text=f"<b>{fmt_number(g['sessions'].sum())}</b><br>"
                                                 f"<span style='font-size:9px;color:{C['ink3']}'>Sessions</span>",
                                            x=0.5, y=0.5, font_size=14, showarrow=False, font_color=C["ink"])])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        tot_s = g["sessions"].sum()
        leg = ""
        for i, (_, r) in enumerate(g.head(8).iterrows()):
            p = r["sessions"] / tot_s * 100 if tot_s else 0
            leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{palette[i%len(palette)]}"></span>'
                    f'<span class="legend-name">{r["session_default_channel_group"]}</span>'
                    f'<span class="legend-pct">{p:.1f}%</span>'
                    f'<span class="legend-val">{fmt_currency(r["purchase_revenue"])}</span></div>')
        st.markdown(leg, unsafe_allow_html=True)
    except Exception as e:
        st.info("مفيش بيانات قنوات في الفترة دي.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW — DEVICES  +  NEW vs RETURNING  +  LANDING PAGES
# ══════════════════════════════════════════════════════════
st.markdown(sec("👥 Audience & Behaviour"), unsafe_allow_html=True)
r2a, r2b, r2c = st.columns([1, 1, 1.6])

with r2a:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Device Category</div>', unsafe_allow_html=True)
    try:
        df_dev = apply_scope(load_dim(str(d_from), str(d_to), ["devicecategory"],
                                      ["sessions", "purchase_revenue", "transactions"]))
        g = df_dev.groupby("devicecategory", as_index=False).agg(
            {"sessions": "sum", "purchase_revenue": "sum", "transactions": "sum"})
        g = g[g["sessions"] > 0].sort_values("sessions", ascending=False)
        dcolors = {"mobile": C["blue"], "desktop": C["green"], "tablet": C["purple"], "smart tv": C["amber"]}
        cols_d = [dcolors.get(str(x).lower(), C["ink3"]) for x in g["devicecategory"]]
        fig = go.Figure(go.Pie(labels=g["devicecategory"], values=g["sessions"], hole=0.66,
                               marker=dict(colors=cols_d, line=dict(color="#fff", width=2)),
                               textinfo="none", sort=False,
                               hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=165,
                          margin=dict(l=0, r=0, t=0, b=0),
                          annotations=[dict(text=f"<b>{fmt_number(g['sessions'].sum())}</b>", x=0.5, y=0.5,
                                            font_size=15, showarrow=False, font_color=C["ink"])])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        ts = g["sessions"].sum()
        leg = ""
        for i, (_, r) in enumerate(g.iterrows()):
            p = r["sessions"] / ts * 100 if ts else 0
            cvr_d = (r["transactions"] / r["sessions"] * 100) if r["sessions"] else 0
            leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{cols_d[i]}"></span>'
                    f'<span class="legend-name">{r["devicecategory"]}</span>'
                    f'<span class="legend-pct">{p:.1f}%</span>'
                    f'<span class="legend-val">CVR {cvr_d:.2f}%</span></div>')
        st.markdown(leg, unsafe_allow_html=True)
    except Exception:
        st.info("مفيش بيانات أجهزة.")
    st.markdown('</div>', unsafe_allow_html=True)

with r2b:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">New vs Returning</div>', unsafe_allow_html=True)
    try:
        df_nr = apply_scope(load_dim(str(d_from), str(d_to), ["new_vs_returning"],
                                     ["sessions", "purchase_revenue", "transactions"]))
        g = df_nr.groupby("new_vs_returning", as_index=False).agg(
            {"sessions": "sum", "purchase_revenue": "sum", "transactions": "sum"})
        g = g[g["sessions"] > 0].sort_values("sessions", ascending=False)
        ncolors = {"new": C["teal"], "returning": C["purple"]}
        cols_n = [ncolors.get(str(x).lower(), C["ink3"]) for x in g["new_vs_returning"]]
        fig = go.Figure(go.Pie(labels=g["new_vs_returning"], values=g["sessions"], hole=0.66,
                               marker=dict(colors=cols_n, line=dict(color="#fff", width=2)),
                               textinfo="none", sort=False,
                               hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=165,
                          margin=dict(l=0, r=0, t=0, b=0),
                          annotations=[dict(text=f"<b>{fmt_number(g['sessions'].sum())}</b>", x=0.5, y=0.5,
                                            font_size=15, showarrow=False, font_color=C["ink"])])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        ts = g["sessions"].sum()
        leg = ""
        for i, (_, r) in enumerate(g.iterrows()):
            p = r["sessions"] / ts * 100 if ts else 0
            cvr_n = (r["transactions"] / r["sessions"] * 100) if r["sessions"] else 0
            leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{cols_n[i]}"></span>'
                    f'<span class="legend-name">{r["new_vs_returning"]}</span>'
                    f'<span class="legend-pct">{p:.1f}%</span>'
                    f'<span class="legend-val">CVR {cvr_n:.2f}%</span></div>')
        st.markdown(leg, unsafe_allow_html=True)
    except Exception:
        st.info("مفيش بيانات New/Returning.")
    st.markdown('</div>', unsafe_allow_html=True)

with r2c:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Top Landing Pages</div>', unsafe_allow_html=True)
    try:
        # page_path is high-cardinality: try the rich call, fall back to sessions only
        df_pp = load_dim(str(d_from), str(d_to), ["page_path"],
                         ["sessions", "purchase_revenue", "transactions"], timeout=75)
        rich = not df_pp.empty and "purchase_revenue" in df_pp.columns
        if df_pp.empty:
            df_pp = load_dim(str(d_from), str(d_to), ["page_path"], ["sessions"], timeout=75)
            rich = False
        df_pp = apply_scope(df_pp)
        agg = {"sessions": "sum"}
        if rich:
            agg.update({"purchase_revenue": "sum", "transactions": "sum"})
        g = df_pp.groupby("page_path", as_index=False).agg(agg)
        g = g[g["sessions"] > 0].sort_values("sessions", ascending=False)
        rows = []
        for _, r in g.head(12).iterrows():
            path = str(r["page_path"])
            short = (path[:46] + "…") if len(path) > 48 else path
            if rich:
                cvr_p = (r["transactions"] / r["sessions"] * 100) if r["sessions"] else 0
                rows.append(f"<tr><td style='font-weight:600' title='{path}'>{short}</td>"
                            f"<td>{fmt_number(r['sessions'])}</td>"
                            f"<td>{fmt_currency(r['purchase_revenue'])}</td>"
                            f"<td>{cvr_p:.2f}%</td></tr>")
            else:
                rows.append(f"<tr><td style='font-weight:600' title='{path}'>{short}</td>"
                            f"<td>{fmt_number(r['sessions'])}</td></tr>")
        head = ("<th>Page</th><th>Sessions</th><th>Revenue</th><th>CVR</th>" if rich
                else "<th>Page</th><th>Sessions</th>")
        st.markdown(f"<table class='styled-table'><thead><tr>{head}</tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    except Exception:
        st.info("مفيش بيانات صفحات.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW — CATEGORY PERFORMANCE
# ══════════════════════════════════════════════════════════
st.markdown(sec("🛍 Product Categories"), unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
try:
    df_cat = apply_scope(load_dim(str(d_from), str(d_to), ["item_category"],
                                  ["item_revenue", "items_purchased", "items_viewed",
                                   "items_added_to_cart"], timeout=75))
    g = df_cat.groupby("item_category", as_index=False).agg(
        {"item_revenue": "sum", "items_purchased": "sum",
         "items_viewed": "sum", "items_added_to_cart": "sum"})
    g = g[g["item_revenue"] > 0].sort_values("item_revenue", ascending=False)
    if g.empty:
        st.info("مفيش بيانات فئات.")
    else:
        rows = []
        for _, r in g.head(12).iterrows():
            v2c = (r["items_added_to_cart"] / r["items_viewed"] * 100) if r["items_viewed"] else 0
            c2p = (r["items_purchased"] / r["items_added_to_cart"] * 100) if r["items_added_to_cart"] else 0
            badge = ('<span class="badge badge-green">قوي</span>' if c2p >= 30 else
                     '<span class="badge badge-amber">متوسط</span>' if c2p >= 10 else
                     '<span class="badge badge-red">ضعيف</span>')
            rows.append(f"<tr><td style='font-weight:600'>{r['item_category']}</td>"
                        f"<td>{fmt_currency(r['item_revenue'])}</td>"
                        f"<td>{fmt_number(r['items_viewed'])}</td>"
                        f"<td>{fmt_number(r['items_added_to_cart'])}</td>"
                        f"<td>{fmt_number(r['items_purchased'])}</td>"
                        f"<td>{v2c:.1f}%</td><td>{c2p:.1f}%</td><td>{badge}</td></tr>")
        st.markdown(
            "<table class='styled-table'><thead><tr><th>Category</th><th>Revenue</th><th>Viewed</th>"
            "<th>Added to Cart</th><th>Purchased</th><th>View→Cart</th><th>Cart→Buy</th><th></th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
except Exception:
    st.info("مفيش بيانات فئات.")
st.markdown('</div>', unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════
#  CAMPAIGNS  +  PRODUCTS BY CAMPAIGN
# ══════════════════════════════════════════════════════════
st.markdown(sec("📣 Campaign Performance", "من GA4 — Meta و Google Ads"), unsafe_allow_html=True)

CAMP_SRC = {"📘 Meta (Facebook/Instagram)": "session_manual_campaign_name",
            "🔵 Google Ads": "session_google_ads_campaign_name"}
camp_choice = st.radio("مصدر الحملات", list(CAMP_SRC.keys()), horizontal=True,
                       key="ga4_camp_src", label_visibility="collapsed")
camp_field = CAMP_SRC[camp_choice]

cmp_l, cmp_r = st.columns([1.3, 1])

with cmp_l:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Campaigns</div>', unsafe_allow_html=True)
    camp_list = []
    try:
        df_cmp = apply_scope(load_dim(str(d_from), str(d_to), [camp_field],
                                      ["sessions", "purchase_revenue", "transactions", "add_to_carts"],
                                      timeout=75))
        g = df_cmp.groupby(camp_field, as_index=False).agg(
            {"sessions": "sum", "purchase_revenue": "sum",
             "transactions": "sum", "add_to_carts": "sum"})
        g = g[g["sessions"] > 0].sort_values("purchase_revenue", ascending=False)
        g = g[~g[camp_field].astype(str).str.lower().isin(["(not set)", "nan", "none", ""])]
        camp_list = g[camp_field].astype(str).tolist()
        if g.empty:
            st.info("مفيش بيانات حملات.")
        else:
            rows = []
            for _, r in g.head(12).iterrows():
                nm = str(r[camp_field]); short = (nm[:38] + "…") if len(nm) > 40 else nm
                cvr_c = (r["transactions"] / r["sessions"] * 100) if r["sessions"] else 0
                aov_c = (r["purchase_revenue"] / r["transactions"]) if r["transactions"] else 0
                badge = ('<span class="badge badge-green">قوي</span>' if cvr_c >= 2 else
                         '<span class="badge badge-amber">متوسط</span>' if cvr_c >= 0.5 else
                         '<span class="badge badge-red">ضعيف</span>')
                rows.append(f"<tr><td style='font-weight:600' title='{nm}'>{short}</td>"
                            f"<td>{fmt_number(r['sessions'])}</td>"
                            f"<td>{fmt_currency(r['purchase_revenue'])}</td>"
                            f"<td>{fmt_number(r['transactions'])}</td>"
                            f"<td>{cvr_c:.2f}%</td><td>{fmt_currency(aov_c,0)}</td><td>{badge}</td></tr>")
            st.markdown(
                "<table class='styled-table'><thead><tr><th>Campaign</th><th>Sessions</th><th>Revenue</th>"
                "<th>Trans.</th><th>CVR</th><th>AOV</th><th></th></tr></thead>"
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
            df_pr = apply_scope(load_dim(str(d_from), str(d_to), [camp_field, "item_name"],
                                         ["item_revenue", "items_purchased", "item_price"],
                                         timeout=90))
            df_pr = df_pr[df_pr[camp_field].astype(str) == sel_camp]
            g = df_pr.groupby("item_name", as_index=False).agg(
                {"item_revenue": "sum", "items_purchased": "sum", "item_price": "mean"})
            g = g[g["item_revenue"] > 0].sort_values("item_revenue", ascending=False)
            if g.empty:
                st.info("مفيش منتجات للكامبين ده.")
            else:
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f'<div style="font-size:11px;color:{C["ink3"]};font-weight:600;">REVENUE</div>'
                                f'<div style="font-size:20px;font-weight:800;color:{C["green"]};">'
                                f'{fmt_currency(g["item_revenue"].sum())}</div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div style="font-size:11px;color:{C["ink3"]};font-weight:600;">PRODUCTS</div>'
                                f'<div style="font-size:20px;font-weight:800;color:{C["blue"]};">'
                                f'{fmt_number(len(g))}</div>', unsafe_allow_html=True)
                rows = []
                for _, r in g.head(10).iterrows():
                    nm = str(r["item_name"]); short = (nm[:34] + "…") if len(nm) > 36 else nm
                    rows.append(f"<tr><td style='font-weight:600' title='{nm}'>{short}</td>"
                                f"<td>{fmt_currency(r['item_revenue'])}</td>"
                                f"<td>{fmt_number(r['items_purchased'])}</td></tr>")
                st.markdown("<table class='styled-table' style='margin-top:10px'><thead><tr><th>Product</th>"
                            "<th>Revenue</th><th>Qty</th></tr></thead>"
                            f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        except Exception:
            st.info("مفيش بيانات منتجات.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  DAILY TABLE + EXPORT
# ══════════════════════════════════════════════════════════
if not daily.empty:
    st.markdown(sec("📋 Daily Performance"), unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    tb = daily.sort_values("date", ascending=False).copy()
    tb["date"] = tb["date"].dt.strftime("%b %d, %Y")
    tb["aov"] = (tb["purchase_revenue"] / tb["transactions"]).replace([float("inf")], 0).fillna(0)
    show_cols = [c for c in ["date", "active_users", "sessions", "items_viewed", "add_to_carts",
                             "checkouts", "transactions", "cvr", "purchase_revenue", "aov"]
                 if c in tb.columns]
    st.dataframe(
        tb[show_cols], use_container_width=True, height=380, hide_index=True,
        column_config={
            "date": st.column_config.TextColumn("Date"),
            "active_users": st.column_config.NumberColumn("Users", format="%,d"),
            "sessions": st.column_config.NumberColumn("Sessions", format="%,d"),
            "items_viewed": st.column_config.NumberColumn("Item Views", format="%,d"),
            "add_to_carts": st.column_config.NumberColumn("Add to Cart", format="%,d"),
            "checkouts": st.column_config.NumberColumn("Checkouts", format="%,d"),
            "transactions": st.column_config.NumberColumn("Transactions", format="%,d"),
            "cvr": st.column_config.NumberColumn("CVR", format="%.2f%%"),
            "purchase_revenue": st.column_config.NumberColumn("Revenue", format="%,.0f"),
            "aov": st.column_config.NumberColumn("AOV", format="%,.0f"),
        },
    )
    buf = io.BytesIO()
    tb[show_cols].to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("📥 Download CSV", buf.getvalue(), "ga4_performance.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("💡 المصدر: GA4 عبر Windsor.ai — Raneen.com (Web) و Raneen Mobile APP.")
