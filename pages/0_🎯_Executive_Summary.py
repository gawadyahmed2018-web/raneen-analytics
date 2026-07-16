"""
Executive Summary — world-class profitability command center for the Analytics Hub.
Source: "Target & Sales Overview" Google Sheet (live via published CSV).

Enterprise BI-grade layout: hero MER gauge, executive health header,
grouped KPI sections (Revenue / Marketing / Efficiency / Operations),
running-total charts, forecast & pace analytics, and an auto-generated
insights feed — styled after Triple Whale / Stripe / Linear.
"""

import io
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from sheets_connector import load_sales_sheet, safe_num, fmt_egp, fmt_number, fmt_pct

st.set_page_config(page_title="Executive Summary", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════
C = {
    "green": "#12B76A", "green_soft": "#D1FADF", "green_dark": "#027A48",
    "amber": "#F79009", "amber_soft": "#FEF0C7", "amber_dark": "#B54708",
    "red": "#F04438", "red_soft": "#FEE4E2", "red_dark": "#B42318",
    "blue": "#2E90FA", "blue_soft": "#D1E9FF", "blue_dark": "#175CD3",
    "purple": "#7A5AF8", "purple_soft": "#EBE9FE", "purple_dark": "#5925DC",
    "ink": "#101828", "ink2": "#475467", "ink3": "#98A2B3",
    "line": "#EAECF0", "bg": "#F9FAFB", "card": "#FFFFFF",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter','IBM Plex Sans Arabic', sans-serif; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 1.2rem 2.4rem 3rem; max-width: 1480px; }}
.stApp {{ background: {C['bg']}; }}

/* ── KPI cards ── */
.kpi {{
  background: {C['card']}; border: 1px solid {C['line']}; border-radius: 20px;
  padding: 22px 24px; position: relative; overflow: hidden; height: 100%;
  box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 1px 3px rgba(16,24,40,.06);
  transition: transform .18s ease, box-shadow .18s ease;
}}
.kpi:hover {{ transform: translateY(-3px); box-shadow: 0 12px 28px rgba(16,24,40,.10); }}
.kpi-top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }}
.kpi-name {{ font-size:12.5px; color:{C['ink2']}; font-weight:600; letter-spacing:.01em; display:flex; align-items:center; gap:7px; }}
.kpi-icon {{ font-size:16px; }}
.kpi-val {{ font-size:34px; font-weight:800; color:{C['ink']}; line-height:1.05; letter-spacing:-.02em; margin-bottom:4px; }}
.kpi-diff {{ font-size:12.5px; font-weight:600; margin-bottom:12px; }}
.kpi-bar-bg {{ background:{C['line']}; border-radius:100px; height:7px; overflow:hidden; margin-bottom:8px; }}
.kpi-bar-fill {{ height:100%; border-radius:100px; transition:width .6s cubic-bezier(.4,0,.2,1); }}
.kpi-foot {{ display:flex; align-items:center; justify-content:space-between; font-size:11.5px; color:{C['ink3']}; }}

/* ── status badge ── */
.badge {{ display:inline-flex; align-items:center; gap:4px; font-size:10.5px; font-weight:700; padding:3px 10px; border-radius:100px; letter-spacing:.02em; }}
.b-green {{ background:{C['green_soft']}; color:{C['green_dark']}; }}
.b-amber {{ background:{C['amber_soft']}; color:{C['amber_dark']}; }}
.b-red {{ background:{C['red_soft']}; color:{C['red_dark']}; }}
.b-blue {{ background:{C['blue_soft']}; color:{C['blue_dark']}; }}

/* ── section title ── */
.sec {{ display:flex; align-items:center; gap:11px; margin:32px 0 16px; }}
.sec-bar {{ width:4px; height:20px; border-radius:100px; }}
.sec-t {{ font-size:17px; font-weight:750; color:{C['ink']}; letter-spacing:-.01em; }}
.sec-s {{ font-size:12px; color:{C['ink3']}; margin-left:auto; font-weight:500; }}

/* ── executive header ── */
.exec-head {{
  background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
  border:1px solid {C['line']}; border-radius:24px; padding:24px 28px; margin-bottom:8px;
  box-shadow: 0 1px 3px rgba(16,24,40,.05);
}}
.health-chip {{ display:flex; flex-direction:column; gap:3px; padding:0 20px; border-left:1px solid {C['line']}; }}
.health-chip:first-child {{ border-left:none; padding-left:0; }}
.health-lbl {{ font-size:11px; color:{C['ink3']}; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }}
.health-val {{ font-size:19px; font-weight:750; }}

/* ── insight callouts ── */
.insight {{ display:flex; align-items:flex-start; gap:12px; padding:14px 18px; border-radius:16px; margin-bottom:10px; border:1px solid transparent; }}
.insight-ico {{ font-size:18px; line-height:1.4; }}
.insight-txt {{ font-size:13.5px; font-weight:500; line-height:1.5; }}
.i-green {{ background:{C['green_soft']}; border-color:#A6F4C5; color:{C['green_dark']}; }}
.i-amber {{ background:{C['amber_soft']}; border-color:#FEDF89; color:{C['amber_dark']}; }}
.i-red {{ background:{C['red_soft']}; border-color:#FECDCA; color:{C['red_dark']}; }}
.i-blue {{ background:{C['blue_soft']}; border-color:#B2DDFF; color:{C['blue_dark']}; }}
.i-purple {{ background:{C['purple_soft']}; border-color:#D9D6FE; color:{C['purple_dark']}; }}

/* ── bars ── */
.bar-row {{ display:flex; align-items:center; gap:12px; margin-bottom:13px; }}
.bar-name {{ font-size:12.5px; color:{C['ink2']}; min-width:120px; font-weight:500; }}
.bar-track {{ flex:1; height:12px; background:{C['line']}; border-radius:100px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:100px; transition:width .6s ease; }}
.bar-val {{ font-size:12.5px; color:{C['ink']}; min-width:120px; text-align:right; font-weight:600; }}

/* ── hero card ── */
.hero {{
  background: linear-gradient(135deg, #101828 0%, #1D2939 100%);
  border-radius:24px; padding:28px 32px; color:#fff; height:100%;
  box-shadow: 0 8px 24px rgba(16,24,40,.18); position:relative; overflow:hidden;
}}
.hero::after {{ content:''; position:absolute; top:-40%; right:-10%; width:280px; height:280px; background:radial-gradient(circle, rgba(122,90,248,.25) 0%, transparent 70%); }}
.hero-lbl {{ font-size:13px; font-weight:600; color:#98A2B3; text-transform:uppercase; letter-spacing:.05em; }}
.hero-val {{ font-size:54px; font-weight:800; letter-spacing:-.03em; line-height:1; margin:6px 0; }}
.hero-sub {{ font-size:13px; color:#D0D5DD; line-height:1.5; }}

@media (max-width: 900px) {{
  .block-container {{ padding: 1rem 1rem 2rem; }}
  .kpi-val {{ font-size:28px; }}
  .hero-val {{ font-size:42px; }}
  .health-chip {{ padding:0 12px; }}
}}
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, IBM Plex Sans Arabic", color=C["ink2"], size=12),
    margin=dict(l=8, r=8, t=36, b=8),
    xaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False),
    yaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="white", bordercolor=C["line"], font_size=12, font_family="Inter"),
)


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def status_of(pct, is_cost=False):
    """Return (badge_class, color, dark, label) for an achievement %."""
    if is_cost:  # lower is better
        if pct <= 100: return "b-green", C["green"], C["green_dark"], "On Track"
        if pct <= 110: return "b-amber", C["amber"], C["amber_dark"], "Watch"
        return "b-red", C["red"], C["red_dark"], "Over"
    else:
        if pct >= 100: return "b-green", C["green"], C["green_dark"], "Above"
        if pct >= 85:  return "b-amber", C["amber"], C["amber_dark"], "Close"
        return "b-red", C["red"], C["red_dark"], "Under"


def spark(values, color, w=110, h=32):
    """Inline SVG sparkline."""
    vals = [safe_num(v) for v in values if v is not None]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    n = len(vals)
    rng = (mx - mn) or 1
    pts = " ".join(
        f"{(i/(n-1))*w:.1f},{h - ((v-mn)/rng)*h:.1f}" for i, v in enumerate(vals)
    )
    last_x = w
    last_y = h - ((vals[-1]-mn)/rng)*h
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h+2}" style="overflow:visible;">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="2.6" fill="{color}"/></svg>'
    )


def trend_arrow(cur, prev):
    """Return (arrow, color) comparing current vs previous."""
    if prev == 0:
        return "→", C["ink3"]
    ch = (cur - prev) / prev * 100
    if ch > 1: return "↑", C["green"]
    if ch < -1: return "↓", C["red"]
    return "→", C["ink3"]


def kpi_card(icon, name, value_str, actual, target, spark_vals, accent,
             is_cost=False, prev_val=None, unit=""):
    """Full executive KPI card: value, target, %, bar, badge, diff, sparkline, arrow."""
    pct = (actual / target * 100) if target else 0
    bcls, col, dark, lbl = status_of(pct, is_cost)
    diff = actual - target
    diff_sign = "+" if diff >= 0 else "−"
    diff_str = f"{diff_sign}{fmt_egp(abs(diff))}" if unit == "egp" else f"{diff_sign}{fmt_number(abs(diff))}"
    bar_w = min(max(pct, 2), 100)
    sp = spark(spark_vals, col) if spark_vals else ""
    arrow, acol = trend_arrow(actual, prev_val) if prev_val is not None else ("", "")
    arrow_html = f'<span style="color:{acol};font-weight:800;font-size:15px;">{arrow}</span>' if arrow else ""
    return (
        f'<div class="kpi">'
        f'<div class="kpi-top"><div class="kpi-name"><span class="kpi-icon">{icon}</span>{name}</div>'
        f'<span class="badge {bcls}">● {lbl}</span></div>'
        f'<div class="kpi-val">{value_str} {arrow_html}</div>'
        f'<div class="kpi-diff" style="color:{col}">{diff_str} vs target</div>'
        f'<div class="kpi-bar-bg"><div class="kpi-bar-fill" style="width:{bar_w}%;background:{col}"></div></div>'
        f'<div class="kpi-foot"><span>Target: {fmt_egp(target) if unit=="egp" else fmt_number(target)}</span>'
        f'<span style="font-weight:700;color:{col}">{pct:.0f}%</span></div>'
        f'<div style="margin-top:10px">{sp}</div>'
        f'</div>'
    )


def simple_card(icon, name, value_str, sub, accent):
    """Lighter KPI card for derived metrics (no target)."""
    return (
        f'<div class="kpi">'
        f'<div class="kpi-top"><div class="kpi-name"><span class="kpi-icon">{icon}</span>{name}</div></div>'
        f'<div class="kpi-val" style="color:{accent}">{value_str}</div>'
        f'<div class="kpi-foot" style="margin-top:8px"><span>{sub}</span></div>'
        f'</div>'
    )


def sec(title, sub="", color=None):
    color = color or C["blue"]
    s = f'<span class="sec-s">{sub}</span>' if sub else ""
    return f'<div class="sec"><div class="sec-bar" style="background:{color}"></div><div class="sec-t">{title}</div>{s}</div>'


def insight(kind, icon, text):
    return f'<div class="insight i-{kind}"><span class="insight-ico">{icon}</span><span class="insight-txt">{text}</span></div>'


# ══════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════
df = load_sales_sheet()
if df.empty:
    st.error("❌ تعذّر تحميل الشيت. تأكد إن الـ Google Sheet منشور (Publish to web).")
    if "_sheet_errors" in st.session_state:
        with st.expander("تفاصيل الخطأ"):
            st.write(st.session_state["_sheet_errors"][-3:])
    st.stop()

df_valid = df[df["Date"].notna() & df["Confirmed Sales"].notna() & (df["Confirmed Sales"] != 0)].copy()
df_valid = df_valid.sort_values("Date")

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🎯 Executive Summary")
    st.caption("المصدر: Target & Sales Overview (Google Sheet)")
    st.markdown("---")
    period = st.selectbox(
        "الفترة",
        ["last_30d", "last_7d", "this_month", "last_month", "last_90d", "all_time", "custom"],
        format_func=lambda x: {
            "last_7d": "آخر 7 أيام", "last_30d": "آخر 30 يوم", "this_month": "الشهر الحالي",
            "last_month": "الشهر الماضي", "last_90d": "آخر 90 يوم", "all_time": "كل الفترة",
            "custom": "فترة مخصصة",
        }.get(x, x),
    )
    max_date = df_valid["Date"].max()
    if period == "custom":
        c_from = st.date_input("من", max_date - timedelta(days=30))
        c_to = st.date_input("إلى", max_date)


def get_period_df(dfv, period):
    max_d = dfv["Date"].max()
    if period == "last_7d":  return dfv[dfv["Date"] >= max_d - timedelta(days=6)]
    if period == "last_30d": return dfv[dfv["Date"] >= max_d - timedelta(days=29)]
    if period == "last_90d": return dfv[dfv["Date"] >= max_d - timedelta(days=89)]
    if period == "this_month":
        return dfv[(dfv["Date"].dt.month == max_d.month) & (dfv["Date"].dt.year == max_d.year)]
    if period == "last_month":
        prev = (max_d.replace(day=1) - timedelta(days=1))
        return dfv[(dfv["Date"].dt.month == prev.month) & (dfv["Date"].dt.year == prev.year)]
    if period == "custom":
        return dfv[(dfv["Date"].dt.date >= c_from) & (dfv["Date"].dt.date <= c_to)]
    return dfv


d = get_period_df(df_valid, period).sort_values("Date")

# Previous equal-length period (for trend arrows)
def get_prev_df(dfv, d):
    if d.empty: return dfv.iloc[0:0]
    length = len(d)
    start_idx = dfv.index.get_indexer([d.index[0]])[0]
    prev_slice = dfv.iloc[max(0, start_idx - length):start_idx]
    return prev_slice


d_prev = get_prev_df(df_valid, d)

if d.empty:
    st.info("مفيش بيانات في الفترة المختارة.")
    st.stop()


# ── Aggregates ──
def agg(frame, col):
    return frame[col].sum() if (not frame.empty and col in frame.columns) else 0

total_spend  = agg(d, "Total Spending");         spend_target = agg(d, "Spending Target")
conf_sales   = agg(d, "Confirmed Sales");         conf_target  = agg(d, "Confirmed Target")
recv_sales   = agg(d, "Received Sales");          recv_target  = agg(d, "Received Target")
retail_sales = agg(d, "Retail Confirmed Sales");  retail_target = agg(d, "Retail Confirmed Target")
mp_sales     = agg(d, "Marketplace Confirmed Sales"); mp_target = agg(d, "Marketplace Confirmed Target")
orders       = agg(d, "No. of Orders")

fb = agg(d, "Facebook Spending"); google = agg(d, "Google Spending"); tiktok = agg(d, "TikTok Spending")
sms = agg(d, "SMS Spending"); criteo = agg(d, "Criteo Spending"); coupons = agg(d, "Coupons"); extra = agg(d, "Extra Spending")

# previous-period equivalents (for arrows)
p_conf = agg(d_prev, "Confirmed Sales"); p_spend = agg(d_prev, "Total Spending")
p_retail = agg(d_prev, "Retail Confirmed Sales"); p_mp = agg(d_prev, "Marketplace Confirmed Sales")

# ── Derived / business KPIs ──
blended_roas = (conf_sales / total_spend) if total_spend else 0
mer = (total_spend / conf_sales * 100) if conf_sales else 0           # Marketing Efficiency Ratio (cost %)
mer_target = 4.0                                                       # target marketing cost %
aov = (conf_sales / orders) if orders else 0
confirm_rate = (conf_sales / recv_sales * 100) if recv_sales else 0

n_days = len(d)
sales_gap = conf_sales - conf_target
budget_remaining = spend_target - total_spend
daily_burn = (total_spend / n_days) if n_days else 0
daily_sales = (conf_sales / n_days) if n_days else 0

# Forecast for current month (only meaningful for this_month)
today = df_valid["Date"].max()
days_in_month = pd.Period(today, freq="M").days_in_month
day_of_month = today.day
month_progress = day_of_month / days_in_month if days_in_month else 0
forecast_sales = (conf_sales / day_of_month * days_in_month) if (period == "this_month" and day_of_month) else conf_sales / n_days * 30
forecast_spend = (total_spend / day_of_month * days_in_month) if (period == "this_month" and day_of_month) else total_spend / n_days * 30
forecast_mer = (forecast_spend / forecast_sales * 100) if forecast_sales else 0
forecast_roas = (forecast_sales / forecast_spend) if forecast_spend else 0

# Pace to target
pace_pct = (conf_sales / conf_target * 100) if conf_target else 0
# required daily to hit target (for this_month)
remaining_target = max(conf_target - conf_sales, 0) if period == "this_month" else 0
days_left = max(days_in_month - day_of_month, 0) if period == "this_month" else 0
required_daily = (remaining_target / days_left) if days_left else 0


# daily series for sparklines
def series(col):
    return d[col].tolist() if col in d.columns else []

sp_sales = series("Confirmed Sales"); sp_spend = series("Total Spending")
sp_retail = series("Retail Confirmed Sales"); sp_mp = series("Marketplace Confirmed Sales")
sp_recv = series("Received Sales")


# ══════════════════════════════════════════════════════════
#  EXECUTIVE HEADER  (period · refresh · health)
# ══════════════════════════════════════════════════════════
p_from = d["Date"].min().date()
p_to = d["Date"].max().date()
refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M")

# health scores
sales_health = pace_pct
mkt_health = 100 - min(max((mer - mer_target) / mer_target * 100, -100), 100) if mer_target else 50
overall_health = (min(sales_health, 130) * 0.6 + max(mkt_health, 0) * 0.4)

def health_word(v, is_sales=True):
    if is_sales:
        if v >= 100: return "Excellent", C["green"]
        if v >= 85:  return "Good", C["amber"]
        return "Needs Focus", C["red"]
    else:
        if v >= 90: return "Efficient", C["green"]
        if v >= 70: return "Moderate", C["amber"]
        return "High Cost", C["red"]

sh_word, sh_col = health_word(sales_health, True)
mh_word, mh_col = health_word(mkt_health, False)
oh_word, oh_col = health_word(overall_health, True)
o_bcls = "b-green" if overall_health >= 100 else "b-amber" if overall_health >= 85 else "b-red"

st.markdown(f"""
<div class="exec-head">
  <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">
    <div style="display:flex; align-items:center; gap:14px;">
      <span style="font-size:32px;">🎯</span>
      <div>
        <div style="font-size:23px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em;">Executive Summary</div>
        <div style="font-size:12.5px; color:{C['ink3']}; margin-top:2px;">📅 {p_from} → {p_to} &nbsp;·&nbsp; 🔄 آخر تحديث {refresh_time}</div>
      </div>
    </div>
    <div style="display:flex; align-items:center;">
      <div class="health-chip"><span class="health-lbl">Sales Health</span><span class="health-val" style="color:{sh_col}">{sh_word}</span></div>
      <div class="health-chip"><span class="health-lbl">Marketing Health</span><span class="health-val" style="color:{mh_col}">{mh_word}</span></div>
      <div class="health-chip"><span class="health-lbl">Overall</span><span class="health-val" style="color:{oh_col}">{oh_word}</span></div>
      <div class="health-chip"><span class="badge {o_bcls}" style="font-size:12px;padding:6px 14px;">● Business {oh_word}</span></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  EXECUTIVE INSIGHTS  (auto-generated, at the TOP)
# ══════════════════════════════════════════════════════════
insights = []

# sales vs target
if conf_target:
    d_pct = (conf_sales / conf_target - 1) * 100
    if d_pct >= 0:
        insights.append(("green", "🎉", f"<b>Confirmed Sales تخطّت التارجت بـ {d_pct:.1f}%</b> — {fmt_egp(conf_sales)} مقابل {fmt_egp(conf_target)} مستهدف."))
    else:
        insights.append(("red", "⚠️", f"<b>Confirmed Sales تحت التارجت بـ {abs(d_pct):.1f}%</b> — محتاج {fmt_egp(abs(sales_gap))} للوصول للتارجت."))

# retail vs marketplace growth
if p_retail and p_mp:
    r_growth = (retail_sales / p_retail - 1) * 100
    m_growth = (mp_sales / p_mp - 1) * 100
    if m_growth > r_growth:
        insights.append(("purple", "📈", f"<b>Marketplace بينمو أسرع من Retail</b> — Marketplace {m_growth:+.1f}% مقابل Retail {r_growth:+.1f}%."))
    else:
        insights.append(("blue", "🏪", f"<b>Retail بينمو أسرع من Marketplace</b> — Retail {r_growth:+.1f}% مقابل Marketplace {m_growth:+.1f}%."))

# marketing cost
mer_word = "تحت" if mer <= mer_target else "فوق"
mer_kind = "green" if mer <= mer_target else "amber"
insights.append((mer_kind, "💰", f"<b>Marketing Cost (MER) = {mer:.2f}%</b> — {mer_word} التارجت ({mer_target:.1f}%). كل 1 جنيه إعلان بيجيب {blended_roas:.1f} جنيه مبيعات."))

# biggest spend channel
spend_map = {"Facebook": fb, "Google": google, "Coupons": coupons, "TikTok": tiktok, "Criteo": criteo, "SMS": sms}
if total_spend:
    top_ch = max(spend_map, key=spend_map.get)
    top_pct = spend_map[top_ch] / total_spend * 100
    kind = "amber" if top_ch == "Coupons" and top_pct > 25 else "blue"
    insights.append((kind, "🎯", f"<b>{top_ch} بيستهلك {top_pct:.0f}% من الميزانية</b> ({fmt_egp(spend_map[top_ch])})" + (" — نسبة عالية من الكوبونات، راجع الهامش." if top_ch=='Coupons' and top_pct>25 else ".")))

# pace / forecast
if period == "this_month" and days_left > 0:
    if pace_pct >= month_progress * 100:
        insights.append(("green", "🚀", f"<b>المعدل الحالي بيوصل للتارجت الشهري</b> — محقق {pace_pct:.0f}% في {day_of_month} يوم. متوقع نهاية الشهر: {fmt_egp(forecast_sales)}."))
    else:
        insights.append(("red", "⏰", f"<b>المعدل الحالي تحت التارجت</b> — محتاج {fmt_egp(required_daily)}/يوم في الـ {days_left} يوم الباقيين للوصول للتارجت."))

st.markdown(sec("💡 Executive Insights", "أهم المؤشرات الآن", C["purple"]), unsafe_allow_html=True)
ins_l, ins_r = st.columns(2)
for i, (kind, icon, txt) in enumerate(insights):
    with (ins_l if i % 2 == 0 else ins_r):
        st.markdown(insight(kind, icon, txt), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  HERO — Marketing Cost % gauge (largest KPI)
# ══════════════════════════════════════════════════════════
st.markdown(sec("⭐ Hero Metric", "المؤشر الأهم للربحية", C["ink"]), unsafe_allow_html=True)
hero_l, hero_r = st.columns([1, 1.3])

with hero_l:
    mer_ok = mer <= mer_target
    mer_col = C["green"] if mer_ok else (C["amber"] if mer <= mer_target * 1.5 else C["red"])
    mer_status = "Excellent" if mer_ok else ("Acceptable" if mer <= mer_target*1.5 else "Too High")
    st.markdown(f"""
    <div class="hero">
      <div class="hero-lbl">Marketing Cost % (MER)</div>
      <div class="hero-val">{mer:.2f}%</div>
      <div style="display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.1);padding:5px 14px;border-radius:100px;font-size:12px;font-weight:600;margin-bottom:14px;">
        <span style="color:{mer_col}">●</span> {mer_status} · Target ≤ {mer_target:.1f}%
      </div>
      <div class="hero-sub">
        إجمالي الصرف ({fmt_egp(total_spend)}) ÷ المبيعات المؤكدة ({fmt_egp(conf_sales)}).<br>
        كل <b style="color:#fff">100 جنيه</b> مبيعات بيكلّف <b style="color:{mer_col}">{mer:.2f} جنيه</b> تسويق · ROAS {blended_roas:.1f}x
      </div>
    </div>
    """, unsafe_allow_html=True)

with hero_r:
    gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=mer,
        number={"suffix": "%", "font": {"size": 40, "color": C["ink"], "family": "Inter"}},
        delta={"reference": mer_target, "increasing": {"color": C["red"]}, "decreasing": {"color": C["green"]}, "suffix": "%"},
        gauge={
            "axis": {"range": [0, max(mer_target*3, mer*1.3)], "tickcolor": C["ink3"]},
            "bar": {"color": mer_col, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, mer_target], "color": C["green_soft"]},
                {"range": [mer_target, mer_target*1.5], "color": C["amber_soft"]},
                {"range": [mer_target*1.5, max(mer_target*3, mer*1.3)], "color": C["red_soft"]},
            ],
            "threshold": {"line": {"color": C["ink"], "width": 3}, "thickness": 0.8, "value": mer_target},
        },
    ))
    gauge.update_layout(**{k: v for k, v in PLOT.items() if k in ("paper_bgcolor", "plot_bgcolor", "font")},
                        height=280, margin=dict(l=20, r=20, t=50, b=10))
    gauge.add_annotation(text="Target", x=0.5, y=0.0, showarrow=False, font=dict(size=11, color=C["ink3"]))
    st.plotly_chart(gauge, use_container_width=True)


# ══════════════════════════════════════════════════════════
#  KPI SECTION 1 — REVENUE
# ══════════════════════════════════════════════════════════
st.markdown(sec("💰 Revenue", "المبيعات مقابل التارجت", C["green"]), unsafe_allow_html=True)
r1, r2, r3, r4 = st.columns(4)
with r1:
    st.markdown(kpi_card("💰", "Confirmed Sales", fmt_egp(conf_sales), conf_sales, conf_target, sp_sales, C["green"], prev_val=p_conf, unit="egp"), unsafe_allow_html=True)
with r2:
    st.markdown(kpi_card("📥", "Received Sales", fmt_egp(recv_sales), recv_sales, recv_target, sp_recv, C["amber"], prev_val=None, unit="egp"), unsafe_allow_html=True)
with r3:
    st.markdown(kpi_card("🏪", "Retail Sales", fmt_egp(retail_sales), retail_sales, retail_target, sp_retail, C["blue"], prev_val=p_retail, unit="egp"), unsafe_allow_html=True)
with r4:
    st.markdown(kpi_card("🛒", "Marketplace Sales", fmt_egp(mp_sales), mp_sales, mp_target, sp_mp, C["purple"], prev_val=p_mp, unit="egp"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  KPI SECTION 2 — MARKETING
# ══════════════════════════════════════════════════════════
st.markdown(sec("📣 Marketing", "الإنفاق والكفاءة", C["blue"]), unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(kpi_card("💸", "Total Spending", fmt_egp(total_spend), total_spend, spend_target, sp_spend, C["red"], is_cost=True, prev_val=p_spend, unit="egp"), unsafe_allow_html=True)
with m2:
    st.markdown(simple_card("📈", "Blended ROAS", f"{blended_roas:.1f}x", "مبيعات ÷ صرف", C["green"]), unsafe_allow_html=True)
with m3:
    st.markdown(simple_card("🎯", "MER (Cost %)", f"{mer:.2f}%", f"Target ≤ {mer_target:.1f}%", C["green"] if mer<=mer_target else C["amber"]), unsafe_allow_html=True)
with m4:
    st.markdown(simple_card("🎟️", "Coupons Share", f"{(coupons/total_spend*100 if total_spend else 0):.0f}%", fmt_egp(coupons), C["amber"]), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  KPI SECTION 3 — EFFICIENCY
# ══════════════════════════════════════════════════════════
st.markdown(sec("⚡ Efficiency", "معدلات الأداء", C["purple"]), unsafe_allow_html=True)
e1, e2, e3, e4 = st.columns(4)
with e1:
    st.markdown(simple_card("✅", "Confirmation Rate", f"{confirm_rate:.1f}%", "Confirmed ÷ Received", C["green"] if confirm_rate>=80 else C["amber"]), unsafe_allow_html=True)
with e2:
    st.markdown(simple_card("🧾", "AOV", fmt_egp(aov, 0), "متوسط قيمة الطلب", C["blue"]), unsafe_allow_html=True)
with e3:
    st.markdown(simple_card("🔥", "Daily Burn Rate", fmt_egp(daily_burn, 0), "متوسط صرف يومي", C["red"]), unsafe_allow_html=True)
with e4:
    st.markdown(simple_card("💵", "Daily Sales", fmt_egp(daily_sales, 0), "متوسط مبيعات يومي", C["green"]), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  KPI SECTION 4 — OPERATIONS
# ══════════════════════════════════════════════════════════
st.markdown(sec("📦 Operations", "الأوردرات والفجوات", C["amber"]), unsafe_allow_html=True)
o1, o2, o3, o4 = st.columns(4)
with o1:
    st.markdown(simple_card("📦", "Orders", fmt_number(orders), "عدد الأوردرات", C["blue"]), unsafe_allow_html=True)
with o2:
    gap_col = C["green"] if sales_gap >= 0 else C["red"]
    st.markdown(simple_card("🎯", "Target Gap", ("+" if sales_gap>=0 else "−")+fmt_egp(abs(sales_gap)), "مبيعات − تارجت", gap_col), unsafe_allow_html=True)
with o3:
    bud_col = C["green"] if budget_remaining >= 0 else C["red"]
    st.markdown(simple_card("💼", "Budget Remaining", ("+" if budget_remaining>=0 else "−")+fmt_egp(abs(budget_remaining)), "تارجت صرف − فعلي", bud_col), unsafe_allow_html=True)
with o4:
    st.markdown(simple_card("📅", "Pace to Target", f"{pace_pct:.0f}%", "من تارجت الفترة", C["green"] if pace_pct>=100 else C["amber"]), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  CHARTS — running totals, pace, forecast
# ══════════════════════════════════════════════════════════
d_ts = d.sort_values("Date").copy()
d_ts["cum_sales"] = d_ts["Confirmed Sales"].cumsum()
d_ts["cum_spend"] = d_ts["Total Spending"].cumsum()
d_ts["cum_target"] = d_ts["Confirmed Target"].cumsum()
d_ts["running_mer"] = (d_ts["cum_spend"] / d_ts["cum_sales"] * 100).fillna(0)
d_ts["running_roas"] = (d_ts["cum_sales"] / d_ts["cum_spend"]).replace([float("inf")], 0).fillna(0)
d_ts["daily_ach"] = (d_ts["Confirmed Sales"] / d_ts["Confirmed Target"] * 100).replace([float("inf")], 0).fillna(0)

st.markdown(sec("📊 Running Performance", "الإجماليات التراكمية", C["blue"]), unsafe_allow_html=True)
cc1, cc2 = st.columns(2)

with cc1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["cum_sales"], name="Running Sales", mode="lines",
                             line=dict(color=C["green"], width=3), fill="tozeroy", fillcolor="rgba(18,183,106,.08)"))
    fig.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["cum_target"], name="Target", mode="lines",
                             line=dict(color=C["ink3"], width=2, dash="dash")))
    fig.update_layout(**PLOT, height=300, title=dict(text="Running Confirmed Sales vs Target", font=dict(size=14, color=C["ink"])))
    st.plotly_chart(fig, use_container_width=True)

with cc2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["cum_spend"], name="Running Spend", mode="lines",
                             line=dict(color=C["red"], width=3), fill="tozeroy", fillcolor="rgba(240,68,56,.06)"))
    fig.add_hline(y=spend_target, line_dash="dash", line_color=C["ink3"], annotation_text="Budget Target", annotation_position="top left")
    fig.update_layout(**PLOT, height=300, title=dict(text="Running Spending vs Budget", font=dict(size=14, color=C["ink"])))
    st.plotly_chart(fig, use_container_width=True)

cc3, cc4 = st.columns(2)
with cc3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["running_mer"], name="Running MER %", mode="lines",
                             line=dict(color=C["purple"], width=3)))
    fig.add_hline(y=mer_target, line_dash="dash", line_color=C["green"], annotation_text=f"Target {mer_target}%", annotation_position="top left")
    fig.update_layout(**PLOT, height=300, title=dict(text="Running MER (Marketing Cost %)", font=dict(size=14, color=C["ink"])))
    st.plotly_chart(fig, use_container_width=True)

with cc4:
    colors = [C["green"] if v >= 100 else (C["amber"] if v >= 85 else C["red"]) for v in d_ts["daily_ach"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d_ts["Date"], y=d_ts["daily_ach"], name="Daily Achievement %", marker_color=colors))
    fig.add_hline(y=100, line_dash="dash", line_color=C["ink3"], annotation_text="100%", annotation_position="top left")
    fig.update_layout(**PLOT, height=300, title=dict(text="Daily Target Achievement %", font=dict(size=14, color=C["ink"])))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════
#  SPENDING BREAKDOWN + SALES SPLIT
# ══════════════════════════════════════════════════════════
b_l, b_r = st.columns([1.3, 1])
with b_l:
    st.markdown(sec("💸 Spending Breakdown", "توزيع الصرف حسب القناة", C["red"]), unsafe_allow_html=True)
    spend_items = [
        ("💙 Facebook", fb, C["blue"]), ("🔵 Google", google, "#4285F4"),
        ("🎟️ Coupons", coupons, C["amber"]), ("⚫ TikTok", tiktok, C["ink"]),
        ("📱 SMS", sms, C["green"]), ("🟣 Criteo", criteo, C["purple"]), ("➕ Extra", extra, C["ink3"]),
    ]
    spend_items = sorted([(n, v, c) for n, v, c in spend_items if v > 0], key=lambda x: x[1], reverse=True)
    mx = max([v for _, v, _ in spend_items]) if spend_items else 1
    for name, val, color in spend_items:
        pct = (val / total_spend * 100) if total_spend else 0
        st.markdown(
            f'<div class="bar-row"><div class="bar-name">{name}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{max(val/mx*100,1)}%;background:{color}"></div></div>'
            f'<div class="bar-val">{fmt_egp(val)} · {pct:.0f}%</div></div>',
            unsafe_allow_html=True,
        )

with b_r:
    st.markdown(sec("🏪 Sales Mix", "Retail vs Marketplace", C["purple"]), unsafe_allow_html=True)
    fig = go.Figure(go.Pie(
        labels=["Retail", "Marketplace"], values=[retail_sales, mp_sales],
        marker=dict(colors=[C["blue"], C["purple"]], line=dict(color="#fff", width=3)),
        hole=0.62, textinfo="label+percent", textfont=dict(size=13, color="#fff", family="Inter"),
    ))
    fig.update_layout(**PLOT, height=290, showlegend=False,
                      annotations=[dict(text=f"{fmt_egp(conf_sales)}<br><span style='font-size:11px;color:{C['ink3']}'>Total</span>",
                                        x=0.5, y=0.5, font_size=15, showarrow=False, font_color=C["ink"])])
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════
#  FORECAST STRIP (this_month only)
# ══════════════════════════════════════════════════════════
if period == "this_month":
    st.markdown(sec("🔮 Forecast & Pace", f"توقعات نهاية الشهر · باقي {days_left} يوم", C["amber"]), unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown(simple_card("🔮", "Forecast Sales", fmt_egp(forecast_sales), f"من تارجت {fmt_egp(conf_target)}", C["green"]), unsafe_allow_html=True)
    with f2:
        st.markdown(simple_card("💸", "Forecast Spend", fmt_egp(forecast_spend), f"من ميزانية {fmt_egp(spend_target)}", C["red"]), unsafe_allow_html=True)
    with f3:
        st.markdown(simple_card("🎯", "Forecast MER", f"{forecast_mer:.2f}%", f"Target ≤ {mer_target:.1f}%", C["green"] if forecast_mer<=mer_target else C["amber"]), unsafe_allow_html=True)
    with f4:
        st.markdown(simple_card("📅", "Required / Day", fmt_egp(required_daily, 0), f"للوصول للتارجت", C["blue"]), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  DAILY PERFORMANCE TABLE  (search · conditional format · sort)
# ══════════════════════════════════════════════════════════
st.markdown(sec("📋 Daily Performance", "تفاصيل يومية", C["ink"]), unsafe_allow_html=True)

tbl = d.sort_values("Date", ascending=False).copy()
tbl["Date"] = tbl["Date"].dt.strftime("%Y-%m-%d")
tbl["MER %"] = (tbl["Total Spending"] / tbl["Confirmed Sales"] * 100).round(2)
tbl["ROAS"] = (tbl["Confirmed Sales"] / tbl["Total Spending"]).round(1)
tbl["Ach %"] = (tbl["Confirmed Sales"] / tbl["Confirmed Target"] * 100).round(0)

show_cols = ["Date", "Confirmed Sales", "Confirmed Target", "Ach %", "Total Spending", "MER %", "ROAS", "No. of Orders"]
show_cols = [c for c in show_cols if c in tbl.columns]
tbl_show = tbl[show_cols].copy()

search = st.text_input("🔍 بحث بالتاريخ (مثلاً 2026-07)", key="tbl_search", placeholder="اكتب جزء من التاريخ...")
if search.strip():
    tbl_show = tbl_show[tbl_show["Date"].str.contains(search.strip(), case=False, na=False)]

st.dataframe(
    tbl_show,
    use_container_width=True, height=420, hide_index=True,
    column_config={
        "Confirmed Sales": st.column_config.NumberColumn("Confirmed Sales", format="%.0f"),
        "Confirmed Target": st.column_config.NumberColumn("Target", format="%.0f"),
        "Ach %": st.column_config.ProgressColumn("Achievement", format="%.0f%%", min_value=0, max_value=150),
        "Total Spending": st.column_config.NumberColumn("Spending", format="%.0f"),
        "MER %": st.column_config.NumberColumn("MER %", format="%.2f%%"),
        "ROAS": st.column_config.NumberColumn("ROAS", format="%.1fx"),
        "No. of Orders": st.column_config.NumberColumn("Orders", format="%d"),
    },
)

buf = io.BytesIO()
d.to_csv(buf, index=False, encoding="utf-8-sig")
st.download_button("📥 Export Period Data (CSV)", buf.getvalue(), "executive_summary.csv", "text/csv")

st.caption("💡 البيانات حيّة من Google Sheet — أي تحديث في الشيت يظهر هنا خلال 5 دقائق (بعد انتهاء الـ cache).")
