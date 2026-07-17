"""
Raneen Executive Dashboard — real-time overview of business performance.
Source: "Target & Sales Overview" Google Sheet (live via published CSV).
Visual design matches the enterprise reference: light theme, soft cards,
AI summary strip, MER gauge, KPI grid with sparklines, running totals,
forecast, budget consumption, and daily performance table.
"""

import io
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from sheets_connector import load_sales_sheet, safe_num, fmt_egp, fmt_number, fmt_pct

st.set_page_config(page_title="Raneen Executive Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════
#  DESIGN TOKENS  (matched to reference image)
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
    "navy": "#0B1120",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter','IBM Plex Sans Arabic', sans-serif; }}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background:rgba(0,0,0,0); }}
.block-container {{ padding: 1rem 1.6rem 3rem; max-width: 1600px; }}
.stApp {{ background: {C['bg']}; }}
[data-testid="stSidebarCollapsedControl"] {{ display: block; }}

/* ═══ TOP BAR ═══ */
.topbar {{
  background: {C['card']}; border:1px solid {C['line']}; border-radius:18px;
  padding:16px 22px; margin-bottom:16px; display:flex; align-items:center;
  justify-content:space-between; gap:16px; flex-wrap:wrap;
  box-shadow:0 1px 3px rgba(15,23,42,.04);
}}
.brand {{ display:flex; align-items:center; gap:13px; }}
.brand-logo {{ width:42px; height:42px; border-radius:11px; background:linear-gradient(135deg,{C['blue']},{C['purple']}); display:flex; align-items:center; justify-content:center; font-size:20px; }}
.brand-t {{ font-size:20px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; display:flex; align-items:center; gap:9px; }}
.brand-s {{ font-size:12px; color:{C['ink3']}; margin-top:1px; }}
.live-dot {{ display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:700; color:{C['green_dark']}; background:{C['green_soft']}; padding:3px 10px; border-radius:100px; }}
.chip {{ background:{C['bg']}; border:1px solid {C['line']}; border-radius:11px; padding:8px 14px; font-size:12.5px; color:{C['ink2']}; font-weight:600; display:inline-flex; align-items:center; gap:7px; }}
.btn-primary {{ background:{C['blue']}; color:#fff; border-radius:11px; padding:8px 16px; font-size:12.5px; font-weight:700; display:inline-flex; align-items:center; gap:6px; }}

/* ═══ CARDS ═══ */
.card {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:20px; box-shadow:0 1px 3px rgba(15,23,42,.04); height:100%; }}
.kpi {{
  background:{C['card']}; border:1px solid {C['line']}; border-radius:16px; padding:16px 17px;
  box-shadow:0 1px 2px rgba(15,23,42,.04); transition:transform .16s, box-shadow .16s; height:100%;
}}
.kpi:hover {{ transform:translateY(-2px); box-shadow:0 10px 24px rgba(15,23,42,.09); }}
.kpi-top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:9px; }}
.kpi-name {{ font-size:12px; color:{C['ink2']}; font-weight:600; display:flex; align-items:center; gap:5px; }}
.kpi-ico {{ width:26px; height:26px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:13px; }}
.kpi-val {{ font-size:26px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; line-height:1.05; }}
.kpi-unit {{ font-size:13px; font-weight:600; color:{C['ink3']}; margin-left:3px; }}
.kpi-meta {{ display:flex; align-items:center; justify-content:space-between; margin-top:5px; font-size:11.5px; }}
.kpi-target {{ color:{C['ink3']}; font-weight:500; }}
.kpi-delta {{ font-weight:700; display:inline-flex; align-items:center; gap:2px; }}

/* ═══ SECTION ═══ */
.sec {{ display:flex; align-items:center; gap:10px; margin:20px 0 13px; }}
.sec-t {{ font-size:16px; font-weight:750; color:{C['ink']}; letter-spacing:-.01em; }}
.sec-s {{ font-size:12px; color:{C['ink3']}; margin-left:auto; }}

/* ═══ AI SUMMARY ═══ */
.ai-box {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:20px 22px; box-shadow:0 1px 3px rgba(15,23,42,.04); }}
.ai-head {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }}
.ai-title {{ font-size:15px; font-weight:750; color:{C['ink']}; display:flex; align-items:center; gap:8px; }}
.ai-health {{ display:inline-flex; align-items:center; gap:7px; background:{C['green_soft']}; color:{C['green_dark']}; padding:5px 12px; border-radius:100px; font-size:12px; font-weight:700; }}
.ai-txt {{ font-size:13.5px; color:{C['ink2']}; line-height:1.7; }}
.ai-txt b {{ color:{C['ink']}; }}
.pill-row {{ display:flex; gap:10px; margin-top:16px; flex-wrap:wrap; }}
.pill {{ flex:1; min-width:110px; background:{C['bg']}; border:1px solid {C['line']}; border-radius:12px; padding:11px 13px; }}
.pill-t {{ font-size:11px; color:{C['ink3']}; font-weight:600; display:flex; align-items:center; gap:5px; }}
.pill-v {{ font-size:12.5px; font-weight:700; margin-top:3px; }}

/* ═══ misc ═══ */
.bar-row {{ display:flex; align-items:center; gap:10px; margin-bottom:11px; }}
.bar-name {{ font-size:12px; color:{C['ink2']}; min-width:95px; font-weight:600; display:flex; align-items:center; gap:6px; }}
.bar-track {{ flex:1; height:8px; background:{C['line']}; border-radius:100px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:100px; }}
.bar-val {{ font-size:12px; color:{C['ink']}; min-width:60px; text-align:right; font-weight:700; }}
.legend-row {{ display:flex; align-items:center; gap:8px; margin-bottom:9px; font-size:12.5px; }}
.legend-dot {{ width:9px; height:9px; border-radius:3px; }}
.legend-name {{ color:{C['ink2']}; font-weight:600; flex:1; }}
.legend-pct {{ color:{C['ink']}; font-weight:700; }}
.legend-val {{ color:{C['ink3']}; min-width:44px; text-align:right; }}
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=C["ink2"], size=11),
    margin=dict(l=6, r=6, t=10, b=6),
    xaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False),
    yaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="white", bordercolor=C["line"], font_size=12),
)


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def spark(values, color, w=150, h=38, fill=True):
    vals = [safe_num(v) for v in values if v is not None]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    n = len(vals)
    pts = [((i/(n-1))*w, h - ((v-mn)/rng)*h) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = ""
    if fill:
        area = (f'<polygon points="0,{h} {line} {w},{h}" fill="{color}" opacity="0.08"/>')
    lx, ly = pts[-1]
    return (
        f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h+3}" preserveAspectRatio="none" style="display:block;">'
        f'{area}<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.8" fill="{color}"/></svg>'
    )


def kpi(icon, name, value, unit, target_str, delta_pct, spark_vals, color, soft,
        is_cost=False, show_target=True, ach_pct=None):
    good = (delta_pct < 0) if is_cost else (delta_pct >= 0)
    dcol = C["green"] if good else C["red"]
    arrow = "▲" if delta_pct >= 0 else "▼"
    sp = spark(spark_vals, color) if spark_vals else ""
    target_html = (
        f'<span class="kpi-target">Target: {target_str}</span>'
        f'<span class="kpi-delta" style="color:{dcol}">{arrow} {abs(delta_pct):.1f}%</span>'
    ) if show_target else (
        f'<span class="kpi-target">{target_str}</span>'
        f'<span class="kpi-delta" style="color:{dcol}">{arrow} {abs(delta_pct):.1f}%</span>'
    )
    # achievement bar + label (only when a target achievement % is provided)
    ach_html = ""
    if ach_pct is not None:
        if is_cost:
            acol = C["green"] if ach_pct <= 100 else (C["amber"] if ach_pct <= 110 else C["red"])
        else:
            acol = C["green"] if ach_pct >= 100 else (C["amber"] if ach_pct >= 85 else C["red"])
        bar_w = min(max(ach_pct, 2), 100)
        ach_html = (
            f'<div style="margin-top:9px;"><div style="display:flex;justify-content:space-between;font-size:10.5px;margin-bottom:3px;">'
            f'<span style="color:{C["ink3"]};font-weight:600;">تحقيق التارجت</span>'
            f'<span style="color:{acol};font-weight:800;">{ach_pct:.0f}%</span></div>'
            f'<div style="height:6px;background:{C["line"]};border-radius:100px;overflow:hidden;">'
            f'<div style="width:{bar_w}%;height:100%;background:{acol};border-radius:100px;"></div></div></div>'
        )
    return (
        f'<div class="kpi"><div class="kpi-top">'
        f'<div class="kpi-name"><span class="kpi-ico" style="background:{soft};color:{color}">{icon}</span>{name}</div>'
        f'</div>'
        f'<div class="kpi-val">{value}<span class="kpi-unit">{unit}</span></div>'
        f'<div class="kpi-meta">{target_html}</div>'
        f'{ach_html}'
        f'<div style="margin-top:8px">{sp}</div></div>'
    )


def sec(title, sub=""):
    s = f'<span class="sec-s">{sub}</span>' if sub else ""
    return f'<div class="sec"><div class="sec-t">{title}</div>{s}</div>'


# ══════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════
df = load_sales_sheet()
if df.empty:
    st.error("❌ تعذّر تحميل الشيت. تأكد إن الـ Google Sheet منشور (Publish to web).")
    st.stop()

df_valid = df[df["Date"].notna() & df["Confirmed Sales"].notna() & (df["Confirmed Sales"] != 0)].copy().sort_values("Date")

min_date = df_valid["Date"].min()
max_date = df_valid["Date"].max()

with st.sidebar:
    st.markdown("## 📊 Executive")
    st.caption("Target & Sales Overview")
    st.markdown("---")
    period = st.selectbox(
        "الفترة",
        ["last_30d", "last_7d", "this_month", "last_month", "last_90d", "all_time", "custom"],
        format_func=lambda x: {
            "last_7d": "آخر 7 أيام", "last_30d": "آخر 30 يوم", "this_month": "الشهر الحالي",
            "last_month": "الشهر الماضي", "last_90d": "آخر 90 يوم", "all_time": "كل الفترة",
            "custom": "📅 تواريخ مخصصة",
        }.get(x, x),
    )

    # Real date-range picker — always visible, pre-filled from the chosen preset
    def _preset_bounds(p):
        if p == "last_7d":  return (max_date - timedelta(days=6)).date(), max_date.date()
        if p == "last_30d": return (max_date - timedelta(days=29)).date(), max_date.date()
        if p == "last_90d": return (max_date - timedelta(days=89)).date(), max_date.date()
        if p == "this_month":
            return max_date.replace(day=1).date(), max_date.date()
        if p == "last_month":
            last = (max_date.replace(day=1) - timedelta(days=1))
            return last.replace(day=1).date(), last.date()
        if p == "all_time": return min_date.date(), max_date.date()
        return (max_date - timedelta(days=29)).date(), max_date.date()

    default_from, default_to = _preset_bounds(period)

    st.markdown("---")
    st.markdown("**📅 نطاق التاريخ**")
    date_range = st.date_input(
        "اختر الفترة",
        value=(default_from, default_to),
        min_value=min_date.date(),
        max_value=max_date.date(),
        format="YYYY-MM-DD",
        label_visibility="collapsed",
        key=f"dr_{period}",
    )
    # date_input returns a tuple once both ends are chosen; guard the mid-selection state
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        c_from, c_to = date_range[0], date_range[1]
    else:
        c_from, c_to = default_from, default_to


def get_period_df(dfv, c_from, c_to):
    return dfv[(dfv["Date"].dt.date >= c_from) & (dfv["Date"].dt.date <= c_to)]


d = get_period_df(df_valid, c_from, c_to).sort_values("Date")
if d.empty:
    st.info("مفيش بيانات في الفترة المختارة.")
    st.stop()

# previous equal-length period
length = len(d)
start_idx = df_valid.index.get_indexer([d.index[0]])[0]
d_prev = df_valid.iloc[max(0, start_idx - length):start_idx]


def a(frame, col):
    return frame[col].sum() if (not frame.empty and col in frame.columns) else 0

total_spend = a(d, "Total Spending"); spend_target = a(d, "Spending Target")
conf_sales = a(d, "Confirmed Sales"); conf_target = a(d, "Confirmed Target")
recv_sales = a(d, "Received Sales"); recv_target = a(d, "Received Target")
retail_sales = a(d, "Retail Confirmed Sales"); retail_target = a(d, "Retail Confirmed Target")
mp_sales = a(d, "Marketplace Confirmed Sales"); mp_target = a(d, "Marketplace Confirmed Target")
orders = a(d, "No. of Orders")
fb = a(d, "Facebook Spending"); google = a(d, "Google Spending"); tiktok = a(d, "TikTok Spending")
sms = a(d, "SMS Spending"); criteo = a(d, "Criteo Spending"); coupons = a(d, "Coupons"); extra = a(d, "Extra Spending")

# previous
p_conf = a(d_prev, "Confirmed Sales"); p_spend = a(d_prev, "Total Spending")
p_recv = a(d_prev, "Received Sales"); p_retail = a(d_prev, "Retail Confirmed Sales")
p_mp = a(d_prev, "Marketplace Confirmed Sales"); p_orders = a(d_prev, "No. of Orders")

# derived
blended_roas = (conf_sales / total_spend) if total_spend else 0
p_roas = (p_conf / p_spend) if p_spend else 0
mer = (total_spend / conf_sales * 100) if conf_sales else 0
# MER target = Spending Target ÷ Confirmed Target (same ratio, using targets)
mer_target = (spend_target / conf_target * 100) if conf_target else 4.0
aov = (conf_sales / orders) if orders else 0
p_aov = (p_conf / p_orders) if p_orders else 0
confirm_rate = (conf_sales / recv_sales * 100) if recv_sales else 0
p_confirm = (p_conf / p_recv * 100) if p_recv else 0
n_days = len(d)
daily_burn = total_spend / n_days if n_days else 0
daily_sales = conf_sales / n_days if n_days else 0
sales_gap = conf_sales - conf_target
budget_remaining = spend_target - total_spend
pace_pct = (conf_sales / conf_target * 100) if conf_target else 0

# forecast
today = df_valid["Date"].max()
dim = pd.Period(today, freq="M").days_in_month
dom = today.day
days_left = max(dim - dom, 0)
if period == "this_month" and dom:
    forecast_sales = conf_sales / dom * dim
    forecast_spend = total_spend / dom * dim
else:
    forecast_sales = daily_sales * 30
    forecast_spend = daily_burn * 30
forecast_mer = (forecast_spend / forecast_sales * 100) if forecast_sales else 0
forecast_roas = (forecast_sales / forecast_spend) if forecast_spend else 0
remaining_target = max(conf_target - conf_sales, 0)
required_daily = (remaining_target / days_left) if days_left else 0
budget_used_pct = (total_spend / spend_target * 100) if spend_target else 0


def series(col):
    return d[col].tolist() if col in d.columns else []

def pct(cur, prev):
    if prev == 0: return 0.0
    return (cur - prev) / prev * 100


# ══════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════
p_from = d["Date"].min().date()
p_to = d["Date"].max().date()
pv_from = d_prev["Date"].min().date() if not d_prev.empty else "—"
pv_to = d_prev["Date"].max().date() if not d_prev.empty else "—"

st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-logo">📊</div>
    <div>
      <div class="brand-t">Raneen Executive Dashboard <span class="live-dot">● Live</span></div>
      <div class="brand-s">Real-time overview of business performance</div>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
    <span class="chip">📅 {p_from} → {p_to}</span>
    <span class="chip">🔄 Compare: {pv_from} → {pv_to}</span>
    <span class="chip">🕐 {datetime.now().strftime('%H:%M')}</span>
    <span class="chip" style="color:{C['green_dark']};background:{C['green_soft']};border-color:#A6F4C5;">🟢 Live · Google Sheet</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  ROW 1 — AI SUMMARY  +  MER GAUGE
# ══════════════════════════════════════════════════════════
row1_l, row1_r = st.columns([2, 1])

with row1_l:
    # business health score
    sales_h = min(pace_pct, 130)
    mer_h = max(0, 100 - max((mer - mer_target) / mer_target * 100, 0))
    health = int(sales_h * 0.6 + mer_h * 0.4)
    health = min(health, 100)

    # dynamic summary text
    sales_dpct = (conf_sales / conf_target - 1) * 100 if conf_target else 0
    retail_share = (retail_sales / conf_sales * 100) if conf_sales else 0
    google_growth = pct(google, a(d_prev, "Google Spending"))
    coupon_over = (coupons / (a(d, "Spending Target") * 0.3) - 1) * 100 if spend_target else 0

    parts = []
    if sales_dpct >= 0:
        parts.append(f'<b>Confirmed Sales</b> are above target by <b>{sales_dpct:.1f}%</b> with {fmt_egp(conf_sales)}.')
    else:
        parts.append(f'<b>Confirmed Sales</b> are below target by <b>{abs(sales_dpct):.1f}%</b> at {fmt_egp(conf_sales)}.')
    parts.append(f'<b>Marketing Cost</b> is {"healthy" if mer<=mer_target else "elevated"} at <b>{mer:.1f}%</b> (target &lt; {mer_target:.0f}%).')
    lead = "Retail" if retail_share >= 50 else "Marketplace"
    lead_share = retail_share if retail_share >= 50 else (100 - retail_share)
    parts.append(f'<b>{lead}</b> continues to lead with <b>{lead_share:.1f}%</b> share.')
    if abs(google_growth) > 3:
        parts.append(f'Google efficiency {"improved" if google_growth>0 else "declined"} by {abs(google_growth):.1f}%.')

    summary = " ".join(parts)

    # pills
    def pill(icon, title, val, color):
        return f'<div class="pill"><div class="pill-t">{icon} {title}</div><div class="pill-v" style="color:{color}">{val}</div></div>'

    pills = "".join([
        pill("💰", "Revenue", "Above Target" if sales_dpct >= 0 else "Below Target", C["green"] if sales_dpct>=0 else C["red"]),
        pill("🎯", "Marketing Cost", "Healthy" if mer <= mer_target else "Elevated", C["green"] if mer<=mer_target else C["amber"]),
        pill("🏪", "Retail", "Strong" if retail_share >= 50 else "Growing", C["blue"]),
        pill("🛒", "Marketplace", "Growing", C["purple"]),
        pill("🔮", "Forecast", "Positive" if forecast_sales >= conf_target else "Watch", C["teal"] if forecast_sales>=conf_target else C["amber"]),
    ])

    hcol = C["green"] if health >= 85 else (C["amber"] if health >= 70 else C["red"])
    hsoft = C["green_soft"] if health >= 85 else (C["amber_soft"] if health >= 70 else C["red_soft"])
    st.markdown(f"""
    <div class="ai-box">
      <div class="ai-head">
        <div class="ai-title">🤖 AI Executive Summary</div>
        <div class="ai-health" style="background:{hsoft};color:{hcol}">Business Health &nbsp;<b>{health}/100</b></div>
      </div>
      <div class="ai-txt">{summary}</div>
      <div class="pill-row">{pills}</div>
    </div>
    """, unsafe_allow_html=True)

with row1_r:
    mer_ok = mer <= mer_target
    mer_col = C["green"] if mer_ok else (C["amber"] if mer <= mer_target*1.5 else C["red"])
    st.markdown(f'<div class="card" style="padding-bottom:6px;"><div style="text-align:center;font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:2px;">Marketing Cost % ⓘ</div>', unsafe_allow_html=True)
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=mer,
        number={"suffix": "%", "font": {"size": 40, "color": C["ink"], "family": "Inter"}},
        gauge={
            "axis": {"range": [0, max(mer_target*3, mer*1.3)], "tickwidth": 1, "tickcolor": C["ink3"], "tickfont": {"size": 9}},
            "bar": {"color": "rgba(0,0,0,0)"},
            "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [
                {"range": [0, mer_target*0.75], "color": C["green"]},
                {"range": [mer_target*0.75, mer_target], "color": "#84E1BC"},
                {"range": [mer_target, mer_target*1.5], "color": C["amber"]},
                {"range": [mer_target*1.5, max(mer_target*3, mer*1.3)], "color": C["red"]},
            ],
            "threshold": {"line": {"color": C["blue"], "width": 5}, "thickness": 0.9, "value": mer_target},
        },
    ))
    gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"), height=200, margin=dict(l=18, r=18, t=8, b=0))
    st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})
    status_txt = "Within Target" if mer_ok else ("Slightly High" if mer <= mer_target*1.5 else "Over Budget")
    st.markdown(f'<div style="text-align:center;margin-top:-8px;padding-bottom:10px;">'
                f'<span style="display:inline-block;background:{C["blue_soft"]};color:{C["blue_dark"]};font-size:16px;font-weight:800;padding:4px 16px;border-radius:100px;">🎯 Target: {mer_target:.1f}%</span><br>'
                f'<span style="display:inline-flex;align-items:center;gap:5px;color:{mer_col};font-weight:700;font-size:13px;margin-top:8px;">✓ {status_txt}</span></div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 2 — KPI GRID  (6 + 6 cards, matching reference)
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# Row A: Confirmed / Received / Spend / MER / ROAS / Orders
a1, a2, a3, a4, a5, a6 = st.columns(6)
with a1:
    st.markdown(kpi("💰", "Confirmed Sales", fmt_egp(conf_sales).replace(" ج",""), "EGP",
                    fmt_egp(conf_target).replace(" ج",""), pct(conf_sales, p_conf), series("Confirmed Sales"),
                    C["green"], C["green_soft"], ach_pct=(conf_sales/conf_target*100 if conf_target else 0)), unsafe_allow_html=True)
with a2:
    st.markdown(kpi("📥", "Received Sales", fmt_egp(recv_sales).replace(" ج",""), "EGP",
                    fmt_egp(recv_target).replace(" ج",""), pct(recv_sales, p_recv), series("Received Sales"),
                    C["teal"], "#CCFBF1", ach_pct=(recv_sales/recv_target*100 if recv_target else 0)), unsafe_allow_html=True)
with a3:
    st.markdown(kpi("💸", "Marketing Spend", fmt_egp(total_spend).replace(" ج",""), "EGP",
                    fmt_egp(spend_target).replace(" ج",""), pct(total_spend, p_spend), series("Total Spending"),
                    C["red"], C["red_soft"], is_cost=True, ach_pct=(total_spend/spend_target*100 if spend_target else 0)), unsafe_allow_html=True)
with a4:
    st.markdown(kpi("🎯", "MER", f"{blended_roas:.1f}", "x",
                    "> 20x", pct(blended_roas, p_roas), series("Confirmed Sales"),
                    C["blue"], C["blue_soft"]), unsafe_allow_html=True)
with a5:
    roas_series = [ (d["Confirmed Sales"].iloc[i]/d["Total Spending"].iloc[i]) if d["Total Spending"].iloc[i] else 0 for i in range(len(d))]
    st.markdown(kpi("📈", "ROAS", f"{blended_roas:.1f}", "x",
                    "> 12x", pct(blended_roas, p_roas), roas_series,
                    C["green"], C["green_soft"]), unsafe_allow_html=True)
with a6:
    st.markdown(kpi("📦", "Orders", fmt_number(orders), "",
                    "28.0K", pct(orders, p_orders), series("No. of Orders"),
                    C["purple"], C["purple_soft"]), unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# Row B: Retail / Marketplace / AOV / Conversion / Pace / Remaining
b1, b2, b3, b4, b5, b6 = st.columns(6)
with b1:
    st.markdown(kpi("🏪", "Retail Sales", fmt_egp(retail_sales).replace(" ج",""), "EGP",
                    f"{(retail_sales/conf_sales*100 if conf_sales else 0):.1f}% of total", pct(retail_sales, p_retail),
                    series("Retail Confirmed Sales"), C["blue"], C["blue_soft"], show_target=False,
                    ach_pct=(retail_sales/retail_target*100 if retail_target else 0)), unsafe_allow_html=True)
with b2:
    st.markdown(kpi("🛒", "Marketplace Sales", fmt_egp(mp_sales).replace(" ج",""), "EGP",
                    f"{(mp_sales/conf_sales*100 if conf_sales else 0):.1f}% of total", pct(mp_sales, p_mp),
                    series("Marketplace Confirmed Sales"), C["purple"], C["purple_soft"], show_target=False,
                    ach_pct=(mp_sales/mp_target*100 if mp_target else 0)), unsafe_allow_html=True)
with b3:
    st.markdown(kpi("🧾", "AOV", fmt_egp(aov,0).replace(" ج",""), "EGP",
                    "Avg. Order Value", pct(aov, p_aov), None,
                    C["amber"], C["amber_soft"], show_target=False), unsafe_allow_html=True)
with b4:
    st.markdown(kpi("✅", "Confirmation Rate", f"{confirm_rate:.1f}", "%",
                    "Confirmed ÷ Received", pct(confirm_rate, p_confirm), None,
                    C["teal"], "#CCFBF1", show_target=False), unsafe_allow_html=True)
with b5:
    pace_col = C["green"] if pace_pct >= 100 else C["amber"]
    st.markdown(f'<div class="kpi"><div class="kpi-top"><div class="kpi-name"><span class="kpi-ico" style="background:{C["green_soft"]};color:{C["green"]}">📅</span>Pace to Target</div></div>'
                f'<div class="kpi-val">{pace_pct:.0f}<span class="kpi-unit">%</span></div>'
                f'<div class="kpi-meta"><span class="kpi-target">{"On Track" if pace_pct>=100 else "Behind"}</span></div>'
                f'<div class="kpi-bar-bg" style="margin-top:9px;background:{C["line"]};border-radius:100px;height:8px;overflow:hidden;"><div style="width:{min(pace_pct,100)}%;height:100%;background:{pace_col};border-radius:100px;"></div></div></div>', unsafe_allow_html=True)
with b6:
    gap_col = C["green"] if sales_gap >= 0 else C["red"]
    gap_txt = "Target Exceeded" if sales_gap >= 0 else "Below Target"
    st.markdown(kpi("🎁", "Target Gap", ("+" if sales_gap>=0 else "−")+fmt_egp(abs(sales_gap)).replace(" ج",""), "EGP",
                    gap_txt, pct(conf_sales, conf_target) if conf_target else 0, series("Confirmed Sales"),
                    gap_col, C["green_soft"] if sales_gap>=0 else C["red_soft"], show_target=False), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 3 — Revenue vs Target · Spending Breakdown · Marketing Mix
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
r3c1, r3c2, r3c3 = st.columns([1.15, 1.15, 1])
d_ts = d.sort_values("Date").copy()

with r3c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:10px;">Revenue vs Target Over Time</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["Confirmed Sales"], name="Confirmed Sales", mode="lines+markers",
                             line=dict(color=C["blue"], width=2.5), marker=dict(size=5, color=C["blue"]),
                             fill="tozeroy", fillcolor="rgba(59,130,246,.07)"))
    fig.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["Confirmed Target"], name="Target", mode="lines",
                             line=dict(color=C["ink3"], width=2, dash="dash")))
    fig.update_layout(**PLOT, height=250)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r3c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:10px;">Spending Breakdown</div>', unsafe_allow_html=True)
    fig = go.Figure()
    chans = [("Meta", "Facebook Spending", C["blue"]), ("Google", "Google Spending", C["green"]),
             ("TikTok", "TikTok Spending", C["pink"]), ("Coupons", "Coupons", C["orange"]),
             ("SMS", "SMS Spending", C["purple"]), ("Criteo", "Criteo Spending", C["teal"])]
    for name, col, color in chans:
        if col in d_ts.columns and d_ts[col].sum() > 0:
            fig.add_trace(go.Bar(x=d_ts["Date"], y=d_ts[col], name=name, marker_color=color))
    fig.update_layout(**PLOT, height=250, barmode="stack")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r3c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:10px;">Marketing Mix</div>', unsafe_allow_html=True)
    mix = [("Meta", fb, C["blue"]), ("Google", google, C["green"]), ("TikTok", tiktok, C["pink"]),
           ("Coupons", coupons, C["orange"]), ("Criteo", criteo, C["teal"]), ("SMS", sms, C["purple"])]
    mix = sorted([(n, v, c) for n, v, c in mix if v > 0], key=lambda x: x[1], reverse=True)
    fig = go.Figure(go.Pie(
        labels=[m[0] for m in mix], values=[m[1] for m in mix],
        marker=dict(colors=[m[2] for m in mix], line=dict(color="#fff", width=2)),
        hole=0.66, textinfo="none", sort=False,
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=150, margin=dict(l=0,r=0,t=0,b=0),
                      annotations=[dict(text=f"<b>{fmt_egp(total_spend).replace(' ج','')}</b><br><span style='font-size:9px;color:{C['ink3']}'>EGP</span>",
                                        x=0.5, y=0.5, font_size=15, showarrow=False, font_color=C["ink"])])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    # legend
    leg = ""
    for name, val, color in mix:
        p = (val/total_spend*100) if total_spend else 0
        leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{color}"></span>'
                f'<span class="legend-name">{name}</span><span class="legend-pct">{p:.0f}%</span>'
                f'<span class="legend-val">{fmt_egp(val).replace(" ج","")}</span></div>')
    st.markdown(leg, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 3.5 — Revenue vs Spending (dual axis combo)
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">'
            f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};">Revenue vs Spending Over Time</div>'
            f'<div style="font-size:11px;color:{C["ink3"]};">المبيعات المؤكدة مقابل إجمالي الصرف · Blended ROAS {blended_roas:.1f}x</div></div>',
            unsafe_allow_html=True)
fig_rs = go.Figure()
fig_rs.add_trace(go.Bar(x=d_ts["Date"], y=d_ts["Total Spending"], name="Spending", marker_color="rgba(240,68,56,.65)",
                        hovertemplate="Spend: %{y:,.0f} ج<extra></extra>"))
fig_rs.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["Confirmed Sales"], name="Confirmed Sales", mode="lines",
                            line=dict(color=C["green"], width=3), yaxis="y2",
                            hovertemplate="Sales: %{y:,.0f} ج<extra></extra>"))
_plot_rs = {k: v for k, v in PLOT.items() if k not in ("yaxis",)}
fig_rs.update_layout(**_plot_rs, height=310,
                     yaxis=dict(title="Spending", gridcolor=C["line"], linecolor=C["line"], zeroline=False),
                     yaxis2=dict(title="Confirmed Sales", overlaying="y", side="right", showgrid=False, zeroline=False),
                     hovermode="x unified")
st.plotly_chart(fig_rs, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)
#  ROW 4 — Target Achievement · Forecast · Budget · Running Totals
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
r4c1, r4c2, r4c3, r4c4 = st.columns([1.1, 1.2, 1, 1])

with r4c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:14px;">Target Achievement</div>', unsafe_allow_html=True)
    ach = [("Confirmed Sales", conf_sales, conf_target), ("Received Sales", recv_sales, recv_target),
           ("Retail Sales", retail_sales, retail_target), ("Marketplace Sales", mp_sales, mp_target)]
    for name, act, tgt in ach:
        p = (act/tgt*100) if tgt else 0
        col = C["green"] if p >= 100 else (C["amber"] if p >= 85 else C["red"])
        st.markdown(
            f'<div style="margin-bottom:13px;"><div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px;">'
            f'<span style="color:{C["ink2"]};font-weight:600;">{name}</span>'
            f'<span style="color:{col};font-weight:700;">{p:.0f}%</span></div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{min(p,100)}%;background:{col}"></div></div>'
            f'<div style="font-size:10.5px;color:{C["ink3"]};margin-top:3px;">{fmt_egp(act).replace(" ج","")} / {fmt_egp(tgt).replace(" ج","")}</div></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:12px;">Forecast (End of Month)</div>', unsafe_allow_html=True)
    fc = [("Forecast Sales", fmt_egp(forecast_sales).replace(" ج",""), pct(forecast_sales, conf_target), C["green"]),
          ("Forecast Spend", fmt_egp(forecast_spend).replace(" ج",""), pct(forecast_spend, spend_target), C["red"]),
          ("Forecast MER", f"{forecast_mer:.1f}%", forecast_mer-mer_target, C["purple"]),
          ("Forecast ROAS", f"{forecast_roas:.1f}x", pct(forecast_roas, blended_roas), C["blue"])]
    fc_cols = st.columns(4)
    for col_st, (name, val, dp, color) in zip(fc_cols, fc):
        with col_st:
            st.markdown(f'<div style="background:{C["bg"]};border:1px solid {C["line"]};border-radius:11px;padding:11px 9px;text-align:center;">'
                        f'<div style="font-size:10px;color:{C["ink3"]};font-weight:600;margin-bottom:5px;">{name}</div>'
                        f'<div style="font-size:16px;font-weight:800;color:{C["ink"]};">{val}</div>'
                        f'<div style="font-size:10px;color:{color};font-weight:700;margin-top:3px;">{"▲" if dp>=0 else "▼"} {abs(dp):.1f}% vs Target</div></div>',
                        unsafe_allow_html=True)
    # prediction banner
    pred_col = C["green"] if forecast_sales >= conf_target else C["amber"]
    pred_pct = (forecast_sales/conf_target-1)*100 if conf_target else 0
    st.markdown(f'<div style="background:linear-gradient(135deg,{C["green_soft"]},#fff);border:1px solid #A6F4C5;border-radius:12px;padding:12px 14px;margin-top:11px;">'
                f'<div style="font-size:11px;color:{C["ink3"]};font-weight:600;">Prediction</div>'
                f'<div style="font-size:13px;font-weight:700;color:{pred_col};margin-top:2px;">Target will be {"exceeded" if pred_pct>=0 else "missed"} by {fmt_egp(abs(forecast_sales-conf_target)).replace(" ج","")} EGP ({abs(pred_pct):.1f}%)</div></div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:8px;">Budget Consumption</div>', unsafe_allow_html=True)
    bcol = C["green"] if budget_used_pct <= 100 else C["red"]
    fig = go.Figure(go.Pie(values=[min(budget_used_pct,100), max(100-budget_used_pct,0)], hole=0.72,
                           marker=dict(colors=[bcol, C["line"]]), textinfo="none", sort=False, direction="clockwise"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=140, margin=dict(l=0,r=0,t=0,b=0),
                      annotations=[dict(text=f"<b>{budget_used_pct:.0f}%</b>", x=0.5, y=0.5, font_size=22, showarrow=False, font_color=C["ink"])])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(f'<div style="font-size:11px;color:{C["ink2"]};line-height:1.9;">'
                f'<div style="display:flex;justify-content:space-between;"><span>Remaining Budget</span><b>{fmt_egp(max(budget_remaining,0)).replace(" ج","")} EGP</b></div>'
                f'<div style="display:flex;justify-content:space-between;"><span>Daily Burn Rate</span><b>{fmt_egp(daily_burn,0).replace(" ج","")} EGP</b></div>'
                f'<div style="display:flex;justify-content:space-between;"><span>Days Remaining</span><b>{days_left} Days</b></div></div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4c4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:12px;">Running Totals</div>', unsafe_allow_html=True)
    rt = [("Running Sales", fmt_egp(conf_sales).replace(" ج","")+" EGP", C["green"]),
          ("Running Spend", fmt_egp(total_spend).replace(" ج","")+" EGP", C["red"]),
          ("Running MER", f"{blended_roas:.1f}x", C["purple"]),
          ("Running ROAS", f"{blended_roas:.1f}x", C["blue"])]
    for name, val, color in rt:
        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid {C["line"]};">'
                    f'<span style="font-size:12px;color:{C["ink2"]};font-weight:600;">{name}</span>'
                    f'<span style="font-size:13.5px;color:{color};font-weight:800;">{val}</span></div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  DAILY PERFORMANCE TABLE
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:14px;font-weight:750;color:{C["ink"]};margin-bottom:12px;">Daily Performance</div>', unsafe_allow_html=True)

tbl = d.sort_values("Date", ascending=False).copy()
tbl["Date"] = tbl["Date"].dt.strftime("%b %d, %Y")
tbl["Ach %"] = (tbl["Confirmed Sales"] / tbl["Confirmed Target"] * 100).round(1)
tbl["Mkt %"] = (tbl["Total Spending"] / tbl["Confirmed Sales"] * 100).round(2)
tbl["MER"] = (tbl["Confirmed Sales"] / tbl["Total Spending"]).round(1)
tbl["AOV_c"] = (tbl["Confirmed Sales"] / tbl["No. of Orders"]).round(0)

cols_show = ["Date", "Confirmed Sales", "Received Sales", "Confirmed Target", "Ach %", "Total Spending", "Mkt %", "MER", "No. of Orders", "AOV_c"]
cols_show = [c for c in cols_show if c in tbl.columns]

search = st.text_input("🔍 Search...", key="tbl_search", placeholder="Search by date...", label_visibility="collapsed")
tbl_v = tbl[cols_show].copy()
if search.strip():
    tbl_v = tbl_v[tbl_v["Date"].str.contains(search.strip(), case=False, na=False)]

st.dataframe(
    tbl_v, use_container_width=True, height=440, hide_index=True,
    column_config={
        "Confirmed Sales": st.column_config.NumberColumn("Confirmed Sales", format="%,.0f"),
        "Received Sales": st.column_config.NumberColumn("Received Sales", format="%,.0f"),
        "Confirmed Target": st.column_config.NumberColumn("Target", format="%,.0f"),
        "Ach %": st.column_config.ProgressColumn("Achievement %", format="%.1f%%", min_value=0, max_value=150),
        "Total Spending": st.column_config.NumberColumn("Marketing Spend", format="%,.0f"),
        "Mkt %": st.column_config.NumberColumn("Marketing %", format="%.2f%%"),
        "MER": st.column_config.NumberColumn("MER", format="%.1fx"),
        "No. of Orders": st.column_config.NumberColumn("Orders", format="%,d"),
        "AOV_c": st.column_config.NumberColumn("AOV", format="%,.0f"),
    },
)
buf = io.BytesIO()
d.to_csv(buf, index=False, encoding="utf-8-sig")
st.download_button("📥 Download CSV", buf.getvalue(), "executive_summary.csv", "text/csv")
st.markdown('</div>', unsafe_allow_html=True)

st.caption("💡 البيانات حيّة من Google Sheet — أي تحديث في الشيت يظهر هنا خلال 5 دقائق.")
