"""
Raneen GA4 — Command Center.
Source: Google Analytics 4 (Web + App) via Windsor.ai.

Layout mirrors the approved reference: AI summary + KPI strip + web/app
contribution, customer-journey funnel (table + drop-off chart), traffic
sources, sessions over time, category & product tables, users new/returning,
geography, campaign intelligence, demographics, day/hour heatmap, alerts.
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
.block-container {{ padding:1rem 1.6rem 2.6rem; max-width:1620px; }}
section[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid {C['line']}; }}
section[data-testid="stSidebar"] label {{ color:{C['ink2']} !important; font-size:12px; font-weight:600; }}

.topbar {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:18px; padding:16px 22px;
  margin-bottom:14px; display:flex; align-items:center; justify-content:space-between; gap:16px;
  flex-wrap:wrap; box-shadow:0 1px 3px rgba(15,23,42,.04); }}
.brand-t {{ font-size:21px; font-weight:800; color:{C['ink']}; letter-spacing:-.02em; }}
.brand-s {{ font-size:12.5px; color:{C['ink3']}; margin-top:2px; }}
.live-dot {{ display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:700;
  color:{C['green_dark']}; background:{C['green_soft']}; padding:4px 11px; border-radius:100px; }}
.chip {{ background:{C['bg']}; border:1px solid {C['line']}; border-radius:11px; padding:8px 14px;
  font-size:12.5px; color:{C['ink2']}; font-weight:600; display:inline-flex; align-items:center; gap:7px; }}

.card {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:16px; padding:18px;
  box-shadow:0 1px 3px rgba(15,23,42,.04); height:100%; }}
.card-t {{ font-size:14px; font-weight:750; color:{C['ink']}; margin-bottom:2px; }}
.card-sub {{ font-size:11px; color:{C['ink3']}; font-weight:500; margin-bottom:11px; }}

/* KPI */
.kpi {{ background:{C['card']}; border:1px solid {C['line']}; border-radius:16px; padding:15px 16px;
  box-shadow:0 1px 2px rgba(15,23,42,.04); transition:transform .16s, box-shadow .16s; height:100%; }}
.kpi:hover {{ transform:translateY(-2px); box-shadow:0 10px 24px rgba(15,23,42,.09); }}
.kpi-name {{ font-size:11.5px; color:{C['ink2']}; font-weight:600; display:flex; align-items:center; gap:6px; margin-bottom:8px; }}
.kpi-ico {{ width:24px; height:24px; border-radius:7px; display:flex; align-items:center; justify-content:center; font-size:12px; }}
.kpi-val {{ font-size:26px; font-weight:800; color:{C['ink']}; letter-spacing:-.025em; line-height:1.05; }}
.kpi-delta {{ font-size:12px; font-weight:700; margin-top:4px; }}
.kpi-prev {{ font-size:10.5px; color:{C['ink3']}; margin-top:1px; }}

/* AI summary rows */
.ai-row {{ display:flex; align-items:flex-start; gap:9px; padding:5px 0; font-size:12.5px;
  color:{C['ink2']}; line-height:1.55; }}
.ai-row b {{ color:{C['ink']}; }}
.ai-rec {{ background:{C['blue_soft']}; border:1px solid #B2DDFF; border-radius:11px;
  padding:11px 13px; margin-top:11px; font-size:12px; color:{C['blue_dark']}; line-height:1.6; }}

/* tables */
.tbl {{ width:100%; border-collapse:collapse; font-size:12px; }}
.tbl th {{ background:#F8FAFC; color:{C['ink2']}; font-weight:600; font-size:10.5px; text-transform:uppercase;
  letter-spacing:.03em; padding:8px 9px; border-bottom:1px solid {C['line']}; text-align:left; white-space:nowrap; }}
.tbl td {{ padding:9px; border-bottom:1px solid #F1F5F9; color:{C['ink']}; white-space:nowrap; }}
.tbl tr:hover td {{ background:rgba(46,144,250,.05); }}
.up {{ color:{C['green']}; font-weight:700; }}
.down {{ color:{C['red']}; font-weight:700; }}
.badge {{ display:inline-block; font-size:10px; padding:3px 8px; border-radius:100px; font-weight:700; }}
.badge-green {{ background:{C['green_soft']}; color:{C['green_dark']}; }}
.badge-amber {{ background:{C['amber_soft']}; color:{C['amber_dark']}; }}
.badge-red {{ background:{C['red_soft']}; color:{C['red_dark']}; }}
.badge-blue {{ background:{C['blue_soft']}; color:{C['blue_dark']}; }}

.legend-row {{ display:flex; align-items:center; gap:7px; margin-bottom:7px; font-size:11.5px; }}
.legend-dot {{ width:8px; height:8px; border-radius:3px; }}
.legend-name {{ color:{C['ink2']}; font-weight:600; flex:1; }}
.legend-pct {{ color:{C['ink']}; font-weight:700; min-width:42px; text-align:right; }}
.legend-d {{ min-width:52px; text-align:right; font-size:10.5px; font-weight:700; }}

/* contribution */
.contrib-v {{ font-size:30px; font-weight:800; letter-spacing:-.03em; }}
.contrib-l {{ font-size:11px; color:{C['ink3']}; }}
.alert-row {{ display:flex; align-items:flex-start; gap:9px; padding:9px 0;
  border-bottom:1px solid #F1F5F9; font-size:12px; color:{C['ink2']}; line-height:1.5; }}
.bar-row {{ display:flex; align-items:center; gap:9px; margin-bottom:7px; }}
.bar-name {{ font-size:11.5px; color:{C['ink2']}; min-width:52px; font-weight:600; }}
.bar-track {{ flex:1; height:9px; background:{C['line']}; border-radius:100px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:100px; }}
.bar-val {{ font-size:11px; color:{C['ink']}; min-width:44px; text-align:right; font-weight:700; }}
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=C["ink2"], size=10),
    margin=dict(l=4, r=4, t=8, b=4),
    xaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False, tickfont=dict(size=9)),
    yaxis=dict(gridcolor=C["line"], linecolor=C["line"], zeroline=False, tickfont=dict(size=9)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)",
                font=dict(size=10)),
    hoverlabel=dict(bgcolor="white", bordercolor=C["line"], font_size=11),
)


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def spark(values, color, w=150, h=36):
    vals = [safe_num(v) for v in values if v is not None]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    n = len(vals)
    pts = [((i/(n-1))*w, h - ((v-mn)/rng)*h) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="display:block;">'
            f'<polygon points="0,{h} {line} {w},{h}" fill="{color}" opacity="0.10"/>'
            f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def delta_html(v, invert=False, suffix="%"):
    good = (v < 0) if invert else (v >= 0)
    cls = "up" if good else "down"
    arr = "↑" if v >= 0 else "↓"
    return f'<span class="{cls}">{arr} {abs(v):.1f}{suffix}</span>'


def kpi(icon, name, value, delta, prev_txt, sp_vals, color, soft, invert=False):
    return (f'<div class="kpi">'
            f'<div class="kpi-name"><span class="kpi-ico" style="background:{soft};color:{color}">{icon}</span>{name}</div>'
            f'<div class="kpi-val">{value}</div>'
            f'<div class="kpi-delta">{delta_html(delta, invert)}</div>'
            f'<div class="kpi-prev">{prev_txt}</div>'
            f'<div style="margin-top:9px">{spark(sp_vals, color)}</div></div>')


def pct_change(cur, prev):
    return 0.0 if prev == 0 else (cur - prev) / prev * 100


# ══════════════════════════════════════════════════════════
#  PERIOD & DATA
# ══════════════════════════════════════════════════════════
def preset_range(p):
    t = date.today()
    m = {"last_7d": (t-timedelta(days=7), t-timedelta(days=1)),
         "last_14d": (t-timedelta(days=14), t-timedelta(days=1)),
         "last_30d": (t-timedelta(days=30), t-timedelta(days=1)),
         "last_90d": (t-timedelta(days=90), t-timedelta(days=1)),
         "this_month": (t.replace(day=1), t-timedelta(days=1)),
         "last_month": ((t.replace(day=1)-timedelta(days=1)).replace(day=1), t.replace(day=1)-timedelta(days=1))}
    return m.get(p, m["last_30d"])


def previous_range(a, b):
    a, b = pd.to_datetime(a).date(), pd.to_datetime(b).date()
    n = (b - a).days + 1
    pt = a - timedelta(days=1)
    return str(pt - timedelta(days=n-1)), str(pt)


with st.sidebar:
    st.markdown("## 📊 Google Analytics 4")
    st.caption("Web + App — عبر Windsor.ai")
    st.markdown("---")
    date_preset = st.selectbox(
        "Date Range", ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month"],
        format_func=lambda x: {"last_7d": "Last 7 Days", "last_14d": "Last 14 Days",
                               "last_30d": "Last 30 Days", "last_90d": "Last 90 Days",
                               "this_month": "This Month", "last_month": "Last Month"}.get(x, x))
    _pf, _pt = preset_range(date_preset)
    st.markdown("**📅 نطاق مخصص**")
    _r = st.date_input("الفترة", value=(_pf, _pt), max_value=date.today(), format="YYYY-MM-DD",
                       label_visibility="collapsed", key=f"ga4_dr_{date_preset}")
    if isinstance(_r, (tuple, list)) and len(_r) == 2:
        d_from, d_to = _r
    elif isinstance(_r, (tuple, list)) and len(_r) == 1:
        d_from = d_to = _r[0]
    else:
        d_from = d_to = _r
    st.caption(f"{d_from} → {d_to}")

prev_from, prev_to = previous_range(d_from, d_to)

MET = ["sessions", "active_users", "items_viewed", "add_to_carts",
       "checkouts", "transactions", "purchase_revenue"]
CORE = ["date"] + MET + ["bounce_rate"]


def _num(df, cols):
    if df.empty:
        return df
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    return df


@st.cache_data(ttl=300, show_spinner="Loading GA4 data...")
def load_core(a, b):
    return _num(get_windsor_data(CORE, date_from=a, date_to=b, source="both", timeout=60),
                MET + ["bounce_rate"])


@st.cache_data(ttl=300, show_spinner=False)
def load_dim(a, b, dims, metrics=None, timeout=80):
    m = list(metrics or MET)
    return _num(get_windsor_data(list(dims) + m, date_from=a, date_to=b, source="both", timeout=timeout), m)


df_all = load_core(str(d_from), str(d_to))
df_prev_all = load_core(prev_from, prev_to)

if df_all.empty:
    st.markdown('<div class="topbar"><div><div class="brand-t">Google Analytics 4 — Command Center</div>'
                '<div class="brand-s">Customer behavior & performance overview</div></div></div>',
                unsafe_allow_html=True)
    st.warning("⚠️ لا توجد بيانات من GA4 في الفترة دي.")
    st.stop()

# ── scope tabs ──
SCOPES = {"🔀 All": "both", "🌐 Website": "web", "📱 Mobile App": "app"}
scope_label = st.radio("scope", list(SCOPES.keys()), horizontal=True, key="ga4_scope",
                       label_visibility="collapsed")
scope = SCOPES[scope_label]


def scoped(f):
    if f.empty or scope == "both" or "source" not in f.columns:
        return f
    return f[f["source"] == scope]


def seg(dim, metrics=None, timeout=80):
    try:
        return scoped(load_dim(str(d_from), str(d_to), [dim], metrics, timeout))
    except Exception:
        return pd.DataFrame()


df = scoped(df_all).copy()
df_prev = scoped(df_prev_all).copy()
if df.empty:
    st.info(f"مفيش بيانات لـ {scope_label}.")
    st.stop()


def tot(f, c):
    return f[c].sum() if (not f.empty and c in f.columns) else 0


t_sessions, t_users = tot(df, "sessions"), tot(df, "active_users")
t_rev, t_trans = tot(df, "purchase_revenue"), tot(df, "transactions")
t_views, t_atc, t_chk = tot(df, "items_viewed"), tot(df, "add_to_carts"), tot(df, "checkouts")
p_sessions, p_users = tot(df_prev, "sessions"), tot(df_prev, "active_users")
p_rev, p_trans = tot(df_prev, "purchase_revenue"), tot(df_prev, "transactions")
p_views, p_atc, p_chk = tot(df_prev, "items_viewed"), tot(df_prev, "add_to_carts"), tot(df_prev, "checkouts")

cvr = (t_trans / t_sessions * 100) if t_sessions else 0
p_cvr = (p_trans / p_sessions * 100) if p_sessions else 0
aov = (t_rev / t_trans) if t_trans else 0
p_aov = (p_rev / p_trans) if p_trans else 0

web_rows = df_all[df_all["source"] == "web"] if "source" in df_all.columns else df_all.iloc[0:0]
app_rows = df_all[df_all["source"] == "app"] if "source" in df_all.columns else df_all.iloc[0:0]
pweb_rows = df_prev_all[df_prev_all["source"] == "web"] if "source" in df_prev_all.columns else df_prev_all.iloc[0:0]
papp_rows = df_prev_all[df_prev_all["source"] == "app"] if "source" in df_prev_all.columns else df_prev_all.iloc[0:0]

# daily series (current + previous, for the overlay chart)
def build_daily(frame):
    if frame.empty or "date" not in frame.columns:
        return pd.DataFrame()
    d = frame.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    a = {c: "sum" for c in MET if c in d.columns}
    out = d.dropna(subset=["date"]).groupby("date", as_index=False).agg(a).sort_values("date")
    if {"transactions", "sessions"} <= set(out.columns):
        out["cvr"] = (out["transactions"] / out["sessions"] * 100).replace([np.inf], 0).fillna(0)
    return out


daily = build_daily(df)
daily_prev = build_daily(df_prev)


def dser(c):
    return daily[c].tolist() if (not daily.empty and c in daily.columns) else []


# ══════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div>
    <div class="brand-t">Google Analytics 4 Command Center</div>
    <div class="brand-s">Customer behavior intelligence & website + app performance overview</div>
  </div>
  <div style="display:flex; align-items:center; gap:9px; flex-wrap:wrap;">
    <span class="live-dot">● Live</span>
    <span class="chip">📅 {d_from} → {d_to}</span>
    <span class="chip" style="color:{C['blue_dark']};background:{C['blue_soft']};border-color:#B2DDFF;">
      Compare: {prev_from} → {prev_to}</span>
    <span class="chip">{scope_label}</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 1 — AI SUMMARY · KPIs · WEB vs APP CONTRIBUTION
# ══════════════════════════════════════════════════════════
r1 = st.columns([1.55, 1, 1, 1, 1, 1, 1.55])

with r1[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">✨ AI Executive Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card-sub">vs {prev_from} → {prev_to}</div>', unsafe_allow_html=True)
    d_sess, d_rev, d_cvr = pct_change(t_sessions, p_sessions), pct_change(t_rev, p_rev), pct_change(cvr, p_cvr)
    lines = []
    # top channel driver
    ch_seg = seg("session_default_channel_group")
    top_ch = ""
    if not ch_seg.empty:
        gch = ch_seg.groupby("session_default_channel_group", as_index=False)["sessions"].sum()
        gch = gch.sort_values("sessions", ascending=False)
        if not gch.empty:
            top_ch = f' مدفوع بـ <b>{gch.iloc[0]["session_default_channel_group"]}</b>'
    lines.append(("📊", f'الترافيك {"زاد" if d_sess>=0 else "قل"} بنسبة <b>{abs(d_sess):.1f}%</b>{top_ch}.'))
    lines.append(("💰", f'الإيراد {"نما" if d_rev>=0 else "تراجع"} <b>{abs(d_rev):.1f}%</b> '
                        f'مع AOV <b>{fmt_currency(aov,0)}</b> ({pct_change(aov,p_aov):+.1f}%).'))
    if t_chk and t_atc:
        chk_rate = t_chk / t_atc * 100
        p_chk_rate = (p_chk / p_atc * 100) if p_atc else 0
        lines.append(("🛒", f'الانتقال من السلة للشيك أوت <b>{chk_rate:.1f}%</b> '
                            f'({pct_change(chk_rate, p_chk_rate):+.1f}%).'))
    if scope == "both" and not web_rows.empty and not app_rows.empty:
        w_c = (tot(web_rows,"transactions")/max(tot(web_rows,"sessions"),1))*100
        a_c = (tot(app_rows,"transactions")/max(tot(app_rows,"sessions"),1))*100
        a_share = tot(app_rows,"sessions")/max(tot(df_all,"sessions"),1)*100
        lines.append(("📱", f'التطبيق <b>{a_share:.1f}%</b> من الترافيك بتحويل <b>{a_c:.2f}%</b> '
                            f'مقابل <b>{w_c:.2f}%</b> للويب.'))
    lines.append(("🎯", f'معدل التحويل <b>{cvr:.2f}%</b> ({d_cvr:+.1f}%) من '
                        f'<b>{fmt_number(t_trans)}</b> عملية.'))
    for ico, txt in lines[:5]:
        st.markdown(f'<div class="ai-row"><span>{ico}</span><span>{txt}</span></div>', unsafe_allow_html=True)
    # recommendation
    rec = "راجع خطوة الشيك أوت — أكبر تسريب في الرحلة."
    if t_views and t_atc and (t_atc/t_views*100) < 15:
        rec = "حسّن صفحات المنتج — الانتقال من المشاهدة للسلة أقل من المتوقع."
    elif scope == "both" and not app_rows.empty and not web_rows.empty:
        w_c = (tot(web_rows,"transactions")/max(tot(web_rows,"sessions"),1))*100
        a_c = (tot(app_rows,"transactions")/max(tot(app_rows,"sessions"),1))*100
        if a_c < w_c * 0.8:
            rec = "حسّن تجربة الشراء في التطبيق — تحويله أقل من الويب بفارق واضح."
    st.markdown(f'<div class="ai-rec"><b>توصية:</b> {rec}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

_kpis = [
    ("👤", "Users", fmt_number(t_users), pct_change(t_users, p_users), fmt_number(p_users),
     dser("active_users"), C["blue"], C["blue_soft"], False),
    ("🔗", "Sessions", fmt_number(t_sessions), pct_change(t_sessions, p_sessions), fmt_number(p_sessions),
     dser("sessions"), C["purple"], C["purple_soft"], False),
    ("💵", "Revenue", fmt_currency(t_rev), pct_change(t_rev, p_rev), fmt_currency(p_rev),
     dser("purchase_revenue"), C["green"], C["green_soft"], False),
    ("🛍", "Transactions", fmt_number(t_trans), pct_change(t_trans, p_trans), fmt_number(p_trans),
     dser("transactions"), C["orange"], C["amber_soft"], False),
    ("🎯", "Conversion Rate", f"{cvr:.2f}%", pct_change(cvr, p_cvr), f"{p_cvr:.2f}%",
     dser("cvr"), C["red"], C["red_soft"], False),
]
for i, (ico, nm, val, dl, prv, sp, col, soft, inv) in enumerate(_kpis):
    with r1[i + 1]:
        st.markdown(kpi(ico, nm, val, dl, f"vs {prv}", sp, col, soft, inv), unsafe_allow_html=True)

with r1[6]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Website vs App Contribution</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card-sub">vs {prev_from} → {prev_to}</div>', unsafe_allow_html=True)
    w_u, a_u = tot(web_rows, "active_users"), tot(app_rows, "active_users")
    pw_u, pa_u = tot(pweb_rows, "active_users"), tot(papp_rows, "active_users")
    tot_u = (w_u + a_u) or 1
    w_pct, a_pct = w_u / tot_u * 100, a_u / tot_u * 100
    cc1, cc2, cc3 = st.columns([1, 1, 1])
    with cc1:
        st.markdown(f'<div class="contrib-l">🌐 Website</div>'
                    f'<div class="contrib-v" style="color:{C["blue"]}">{w_pct:.1f}%</div>'
                    f'<div class="contrib-l">of total users</div>'
                    f'<div style="margin-top:3px">{delta_html(pct_change(w_u, pw_u))}</div>',
                    unsafe_allow_html=True)
    with cc2:
        fig = go.Figure(go.Pie(values=[w_u, a_u], labels=["Website", "Mobile App"], hole=0.68,
                               marker=dict(colors=[C["blue"], C["purple"]], line=dict(color="#fff", width=2)),
                               textinfo="none", sort=False,
                               hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=120,
                          margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with cc3:
        st.markdown(f'<div class="contrib-l">📱 Mobile App</div>'
                    f'<div class="contrib-v" style="color:{C["purple"]}">{a_pct:.1f}%</div>'
                    f'<div class="contrib-l">of total users</div>'
                    f'<div style="margin-top:3px">{delta_html(pct_change(a_u, pa_u))}</div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 2 — FUNNEL TABLE · DROP-OFF CHART · TRAFFIC · SESSIONS
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
r2 = st.columns([1.25, 1.25, 1, 1.15])

# funnel stages (current + previous for the vs-previous column)
STAGES = [("🔗", "Session Start", t_sessions, p_sessions),
          ("👁", "View Item", t_views, p_views),
          ("🛒", "Add To Cart", t_atc, p_atc),
          ("💳", "Begin Checkout", t_chk, p_chk),
          ("✅", "Purchase", t_trans, p_trans)]
STAGES = [s for s in STAGES if s[2] > 0]

with r2[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Customer Journey Funnel</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card-sub">vs {prev_from} → {prev_to}</div>', unsafe_allow_html=True)
    if len(STAGES) < 2:
        st.info("مفيش بيانات كافية.")
    else:
        top_v = STAGES[0][2]
        rows = []
        for i, (ico, name, val, pval) in enumerate(STAGES):
            conv = (val / top_v * 100) if top_v else 0
            drop_txt = "–"
            if i > 0:
                prev_stage = STAGES[i-1][2]
                drop = 100 - (val / prev_stage * 100 if prev_stage else 0)
                drop_txt = f'<span class="down">{drop:.1f}%</span>'
            rows.append(f"<tr><td>{ico} <b>{name}</b></td>"
                        f"<td>{fmt_number(val)}</td>"
                        f"<td>{conv:.1f}%</td>"
                        f"<td>{drop_txt}</td>"
                        f"<td>{delta_html(pct_change(val, pval))}</td></tr>")
        st.markdown("<table class='tbl'><thead><tr><th>Stage</th><th>Users</th><th>Conv.</th>"
                    "<th>Drop</th><th>vs Prev</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        st.markdown(f'<div style="margin-top:10px;padding-top:9px;border-top:1px solid {C["line"]};'
                    f'display:flex;justify-content:space-between;align-items:center;font-size:12px;">'
                    f'<span style="color:{C["ink2"]};font-weight:700;">Overall Conversion Rate</span>'
                    f'<span><b style="color:{C["purple"]};font-size:14px;">{cvr:.2f}%</b> '
                    f'{delta_html(pct_change(cvr, p_cvr))}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Funnel Drop-off Visualization</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-sub">حجم كل خطوة ونسبة الفقد بينها</div>', unsafe_allow_html=True)
    if len(STAGES) >= 2:
        names = [s[1] for s in STAGES]
        vals = [s[2] for s in STAGES]
        grad = [C["blue"], C["indigo"], C["purple"], C["orange"], C["green"]]
        fig = go.Figure(go.Bar(x=names, y=vals, marker_color=grad[:len(vals)],
                               text=[fmt_number(v) for v in vals], textposition="outside",
                               hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
        # drop annotations between bars
        for i in range(1, len(vals)):
            drop = 100 - (vals[i] / vals[i-1] * 100 if vals[i-1] else 0)
            fig.add_annotation(x=i - 0.5, y=max(vals) * 0.55, text=f"▼{drop:.1f}%",
                               showarrow=False, font=dict(size=10, color=C["red"]))
        fig.update_layout(**PLOT, height=232)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        # worst step callout
        worst, wd = "", -1
        for i in range(1, len(STAGES)):
            drop = 100 - (STAGES[i][2] / STAGES[i-1][2] * 100 if STAGES[i-1][2] else 0)
            if drop > wd:
                wd, worst = drop, f"{STAGES[i-1][1]} → {STAGES[i][1]}"
        st.markdown(f'<div style="background:{C["red_soft"]};border:1px solid #FECDCA;border-radius:11px;'
                    f'padding:10px 12px;margin-top:6px;">'
                    f'<div style="font-size:10.5px;color:{C["ink3"]};font-weight:600;">Top Drop-off Point</div>'
                    f'<div style="font-size:12.5px;font-weight:700;color:{C["red_dark"]};margin-top:2px;">'
                    f'{worst} · <b>{wd:.1f}%</b></div></div>', unsafe_allow_html=True)
    else:
        st.info("مفيش بيانات كافية.")
    st.markdown('</div>', unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_channel_prev(a, b):
    try:
        return _num(get_windsor_data(["session_default_channel_group", "sessions"],
                                     date_from=a, date_to=b, source="both", timeout=80), ["sessions"])
    except Exception:
        return pd.DataFrame()


with r2[2]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Traffic Sources</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card-sub">vs {prev_from} → {prev_to}</div>', unsafe_allow_html=True)
    ch = seg("session_default_channel_group")
    if ch.empty:
        st.info("مفيش بيانات قنوات.")
    else:
        g = ch.groupby("session_default_channel_group", as_index=False)["sessions"].sum()
        g["session_default_channel_group"] = g["session_default_channel_group"].astype(str)
        g = g[(g["sessions"] > 0) &
              (~g["session_default_channel_group"].str.lower().isin(["(not set)", "nan", "none", ""]))]
        g = g.sort_values("sessions", ascending=False)
        chp = scoped(load_channel_prev(prev_from, prev_to))
        prev_map = {}
        if not chp.empty and "session_default_channel_group" in chp.columns:
            gp = chp.groupby("session_default_channel_group", as_index=False)["sessions"].sum()
            prev_map = dict(zip(gp["session_default_channel_group"].astype(str), gp["sessions"]))
        pal = [C["blue"], C["green"], C["purple"], C["amber"], C["pink"], C["teal"], C["orange"], C["ink3"]]
        fig = go.Figure(go.Pie(labels=g["session_default_channel_group"], values=g["sessions"], hole=0.66,
                               marker=dict(colors=pal[:len(g)], line=dict(color="#fff", width=2)),
                               textinfo="none", sort=False,
                               hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=150,
                          margin=dict(l=0, r=0, t=0, b=0),
                          annotations=[dict(text=f"<b>{fmt_number(g['sessions'].sum())}</b><br>"
                                                 f"<span style='font-size:9px;color:{C['ink3']}'>Sessions</span>",
                                            x=0.5, y=0.5, font_size=13, showarrow=False, font_color=C["ink"])])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        ts = g["sessions"].sum()
        leg = ""
        for i, (_, r) in enumerate(g.head(7).iterrows()):
            nm = r["session_default_channel_group"]
            p = r["sessions"] / ts * 100 if ts else 0
            dlt = pct_change(r["sessions"], prev_map.get(nm, 0))
            leg += (f'<div class="legend-row"><span class="legend-dot" style="background:{pal[i%len(pal)]}"></span>'
                    f'<span class="legend-name">{nm}</span>'
                    f'<span class="legend-pct">{p:.1f}%</span>'
                    f'<span class="legend-d">{delta_html(dlt)}</span></div>')
        st.markdown(leg, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2[3]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Sessions Over Time</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card-sub">هذه الفترة مقابل السابقة</div>', unsafe_allow_html=True)
    if not daily.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(len(daily))), y=daily["sessions"], name="This Period",
                                 mode="lines+markers", line=dict(color=C["blue"], width=2.4),
                                 marker=dict(size=4),
                                 customdata=daily["date"].dt.strftime("%b %d"),
                                 hovertemplate="%{customdata}<br>%{y:,.0f}<extra></extra>"))
        if not daily_prev.empty:
            fig.add_trace(go.Scatter(x=list(range(len(daily_prev))), y=daily_prev["sessions"],
                                     name="Previous", mode="lines",
                                     line=dict(color=C["ink3"], width=1.8, dash="dot"),
                                     customdata=daily_prev["date"].dt.strftime("%b %d"),
                                     hovertemplate="%{customdata}<br>%{y:,.0f}<extra></extra>"))
        _p = {k: v for k, v in PLOT.items() if k != "xaxis"}
        fig.update_layout(**_p, height=248,
                          xaxis=dict(showticklabels=False, gridcolor=C["line"], zeroline=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 3 — CATEGORY · TOP PRODUCTS · USERS · GEOGRAPHY
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
r3 = st.columns([1.15, 1.25, 0.85, 1.05])

with r3[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Category Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-sub">حسب الإيراد</div>', unsafe_allow_html=True)
    cat = seg("item_category", ["item_revenue", "items_purchased", "items_viewed",
                                "items_added_to_cart"], timeout=90)
    if cat.empty or "item_category" not in cat.columns:
        st.info("مفيش بيانات فئات.")
    else:
        g = cat.groupby("item_category", as_index=False).agg(
            {"item_revenue": "sum", "items_purchased": "sum",
             "items_viewed": "sum", "items_added_to_cart": "sum"})
        g["item_category"] = g["item_category"].astype(str)
        g = g[(g["item_revenue"] > 0) &
              (~g["item_category"].str.lower().isin(["(not set)", "nan", "none", ""]))]
        g = g.sort_values("item_revenue", ascending=False)
        rows = []
        for _, r in g.head(8).iterrows():
            c_cvr = (r["items_purchased"] / r["items_viewed"] * 100) if r["items_viewed"] else 0
            c_aov = (r["item_revenue"] / r["items_purchased"]) if r["items_purchased"] else 0
            rows.append(f"<tr><td><b>{r['item_category']}</b></td>"
                        f"<td>{fmt_number(r['items_viewed'])}</td>"
                        f"<td>{fmt_currency(r['item_revenue'])}</td>"
                        f"<td>{c_cvr:.2f}%</td>"
                        f"<td>{fmt_number(r['items_purchased'])}</td>"
                        f"<td>{fmt_currency(c_aov,0)}</td></tr>")
        st.markdown("<table class='tbl'><thead><tr><th>Category</th><th>Views</th><th>Revenue</th>"
                    "<th>CVR</th><th>Sold</th><th>AOV</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r3[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Top Products</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-sub">حسب الإيراد</div>', unsafe_allow_html=True)
    prod = seg("item_name", ["item_revenue", "items_purchased", "items_viewed"], timeout=95)
    if prod.empty or "item_name" not in prod.columns:
        st.info("مفيش بيانات منتجات.")
    else:
        g = prod.groupby("item_name", as_index=False).agg(
            {"item_revenue": "sum", "items_purchased": "sum", "items_viewed": "sum"})
        g["item_name"] = g["item_name"].astype(str)
        g = g[(g["item_revenue"] > 0) & (~g["item_name"].str.lower().isin(["(not set)", "nan", "none", ""]))]
        g = g.sort_values("item_revenue", ascending=False)
        rows = []
        for _, r in g.head(8).iterrows():
            nm = r["item_name"]; short = (nm[:26] + "…") if len(nm) > 28 else nm
            p_cvr = (r["items_purchased"] / r["items_viewed"] * 100) if r["items_viewed"] else 0
            p_aov = (r["item_revenue"] / r["items_purchased"]) if r["items_purchased"] else 0
            rows.append(f"<tr><td title='{nm}'><b>{short}</b></td>"
                        f"<td>{fmt_number(r['items_viewed'])}</td>"
                        f"<td>{fmt_currency(r['item_revenue'])}</td>"
                        f"<td>{fmt_number(r['items_purchased'])}</td>"
                        f"<td>{p_cvr:.2f}%</td><td>{fmt_currency(p_aov,0)}</td></tr>")
        st.markdown("<table class='tbl'><thead><tr><th>Product</th><th>Views</th><th>Revenue</th>"
                    "<th>Sold</th><th>CVR</th><th>AOV</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r3[2]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Users</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-sub">جديد مقابل عائد</div>', unsafe_allow_html=True)
    nr = seg("new_vs_returning", ["sessions", "active_users", "transactions", "purchase_revenue"])
    if nr.empty or "new_vs_returning" not in nr.columns:
        st.info("مفيش بيانات.")
    else:
        g = nr.groupby("new_vs_returning", as_index=False).agg(
            {"active_users": "sum", "sessions": "sum", "transactions": "sum"})
        g["new_vs_returning"] = g["new_vs_returning"].astype(str).str.lower()
        new_u = g[g["new_vs_returning"].str.contains("new")]["active_users"].sum()
        ret_u = g[g["new_vs_returning"].str.contains("return")]["active_users"].sum()
        tu = (new_u + ret_u) or 1
        cA, cB = st.columns(2)
        with cA:
            st.markdown(f'<div style="background:{C["teal_soft"]};border-radius:11px;padding:10px;">'
                        f'<div style="font-size:10.5px;color:{C["ink3"]};font-weight:600;">New Users</div>'
                        f'<div style="font-size:19px;font-weight:800;color:{C["teal"]};">{fmt_number(new_u)}</div>'
                        f'<div style="font-size:10.5px;color:{C["ink3"]};">{new_u/tu*100:.1f}%</div></div>',
                        unsafe_allow_html=True)
        with cB:
            st.markdown(f'<div style="background:{C["purple_soft"]};border-radius:11px;padding:10px;">'
                        f'<div style="font-size:10.5px;color:{C["ink3"]};font-weight:600;">Returning</div>'
                        f'<div style="font-size:19px;font-weight:800;color:{C["purple"]};">{fmt_number(ret_u)}</div>'
                        f'<div style="font-size:10.5px;color:{C["ink3"]};">{ret_u/tu*100:.1f}%</div></div>',
                        unsafe_allow_html=True)
        fig = go.Figure(go.Pie(values=[new_u, ret_u], labels=["New", "Returning"], hole=0.68,
                               marker=dict(colors=[C["teal"], C["purple"]], line=dict(color="#fff", width=2)),
                               textinfo="none", sort=False,
                               hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=132,
                          margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r3[3]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Geographic Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-sub">حسب الجلسات</div>', unsafe_allow_html=True)
    geo = seg("country", ["sessions", "active_users", "purchase_revenue"], timeout=85)
    if geo.empty or "country" not in geo.columns:
        st.info("حقل الدولة غير متاح في الـ connector.")
    else:
        g = geo.groupby("country", as_index=False).agg(
            {"sessions": "sum", "purchase_revenue": "sum"})
        g["country"] = g["country"].astype(str)
        g = g[(g["sessions"] > 0) & (~g["country"].str.lower().isin(["(not set)", "nan", "none", ""]))]
        g = g.sort_values("sessions", ascending=False)
        ts = g["sessions"].sum()
        mx = g["sessions"].max() if not g.empty else 1
        html = ""
        for _, r in g.head(7).iterrows():
            p = r["sessions"] / ts * 100 if ts else 0
            html += (f'<div class="bar-row"><div class="bar-name" style="min-width:78px">{r["country"]}</div>'
                     f'<div class="bar-track"><div class="bar-fill" '
                     f'style="width:{r["sessions"]/mx*100:.0f}%;background:{C["blue"]}"></div></div>'
                     f'<div class="bar-val">{p:.1f}%</div></div>')
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  ROW 4 — CAMPAIGNS · PRODUCTS BY CAMPAIGN · DEMOGRAPHICS ·
#          DAY×HOUR HEATMAP · ALERTS
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
r4 = st.columns([1.35, 1.05, 0.85, 1, 0.95])

CAMP_SRC = {"📘 Meta": "session_manual_campaign_name", "🔵 Google Ads": "session_google_ads_campaign_name"}

with r4[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Campaign Performance Intelligence</div>', unsafe_allow_html=True)
    camp_choice = st.radio("src", list(CAMP_SRC.keys()), horizontal=True,
                           key="ga4_camp_src", label_visibility="collapsed")
    camp_field = CAMP_SRC[camp_choice]
    camp_list = []
    cmp_df = seg(camp_field, ["sessions", "transactions", "purchase_revenue"], timeout=90)
    if cmp_df.empty or camp_field not in cmp_df.columns:
        st.info("مفيش بيانات حملات.")
    else:
        g = cmp_df.groupby(camp_field, as_index=False).agg(
            {"sessions": "sum", "transactions": "sum", "purchase_revenue": "sum"})
        g[camp_field] = g[camp_field].astype(str)
        g = g[(g["sessions"] > 0) & (~g[camp_field].str.lower().isin(["(not set)", "nan", "none", ""]))]
        g = g.sort_values("purchase_revenue", ascending=False)
        camp_list = g[camp_field].tolist()
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div style="font-size:10px;color:{C["ink3"]};font-weight:600;">CAMPAIGNS</div>'
                        f'<div style="font-size:18px;font-weight:800;color:{C["ink"]};">{len(g)}</div>',
                        unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div style="font-size:10px;color:{C["ink3"]};font-weight:600;">REVENUE</div>'
                        f'<div style="font-size:18px;font-weight:800;color:{C["green"]};">'
                        f'{fmt_currency(g["purchase_revenue"].sum())}</div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div style="font-size:10px;color:{C["ink3"]};font-weight:600;">ORDERS</div>'
                        f'<div style="font-size:18px;font-weight:800;color:{C["orange"]};">'
                        f'{fmt_number(g["transactions"].sum())}</div>', unsafe_allow_html=True)
        rows = []
        for _, r in g.head(7).iterrows():
            nm = r[camp_field]; short = (nm[:24] + "…") if len(nm) > 26 else nm
            c_cvr = (r["transactions"] / r["sessions"] * 100) if r["sessions"] else 0
            c_aov = (r["purchase_revenue"] / r["transactions"]) if r["transactions"] else 0
            rows.append(f"<tr><td title='{nm}'><b>{short}</b></td>"
                        f"<td>{fmt_number(r['sessions'])}</td>"
                        f"<td>{fmt_currency(r['purchase_revenue'])}</td>"
                        f"<td>{fmt_number(r['transactions'])}</td>"
                        f"<td>{c_cvr:.2f}%</td><td>{fmt_currency(c_aov,0)}</td></tr>")
        st.markdown("<table class='tbl' style='margin-top:10px'><thead><tr><th>Campaign</th><th>Sessions</th>"
                    "<th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Top Products by Campaign</div>', unsafe_allow_html=True)
    if not camp_list:
        st.info("مفيش حملات.")
    else:
        sel = st.selectbox("campaign", camp_list, key="ga4_prod_camp", label_visibility="collapsed")
        try:
            pc = scoped(load_dim(str(d_from), str(d_to), [camp_field, "item_name"],
                                 ["item_revenue", "items_purchased"], timeout=95))
            pc = pc[pc[camp_field].astype(str) == sel]
            gp = pc.groupby("item_name", as_index=False).agg(
                {"item_revenue": "sum", "items_purchased": "sum"})
            gp = gp[gp["item_revenue"] > 0].sort_values("item_revenue", ascending=False)
            if gp.empty:
                st.info("مفيش منتجات.")
            else:
                rows = []
                for _, r in gp.head(7).iterrows():
                    nm = str(r["item_name"]); short = (nm[:22] + "…") if len(nm) > 24 else nm
                    rows.append(f"<tr><td title='{nm}'><b>{short}</b></td>"
                                f"<td>{fmt_currency(r['item_revenue'])}</td>"
                                f"<td>{fmt_number(r['items_purchased'])}</td></tr>")
                st.markdown("<table class='tbl'><thead><tr><th>Product</th><th>Revenue</th>"
                            f"<th>Qty</th></tr></thead><tbody>{''.join(rows)}</tbody></table>",
                            unsafe_allow_html=True)
        except Exception:
            st.info("مفيش بيانات منتجات.")
    st.markdown('</div>', unsafe_allow_html=True)

with r4[2]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Demographics</div>', unsafe_allow_html=True)
    demo = seg("age", ["sessions", "active_users"], timeout=85)
    gen = seg("gender", ["sessions", "active_users"], timeout=85)
    shown = False
    if not demo.empty and "age" in demo.columns:
        g = demo.groupby("age", as_index=False)["sessions"].sum()
        g["age"] = g["age"].astype(str)
        g = g[(g["sessions"] > 0) & (~g["age"].str.lower().isin(["(not set)", "nan", "none", ""]))]
        g = g.sort_values("age")
        if not g.empty:
            shown = True
            mx = g["sessions"].max()
            ts = g["sessions"].sum()
            html = f'<div style="font-size:10.5px;color:{C["ink3"]};font-weight:600;margin-bottom:6px;">AGE</div>'
            for _, r in g.iterrows():
                html += (f'<div class="bar-row"><div class="bar-name">{r["age"]}</div>'
                         f'<div class="bar-track"><div class="bar-fill" '
                         f'style="width:{r["sessions"]/mx*100:.0f}%;background:{C["blue"]}"></div></div>'
                         f'<div class="bar-val">{r["sessions"]/ts*100:.1f}%</div></div>')
            st.markdown(html, unsafe_allow_html=True)
    if not gen.empty and "gender" in gen.columns:
        g = gen.groupby("gender", as_index=False)["sessions"].sum()
        g["gender"] = g["gender"].astype(str)
        g = g[(g["sessions"] > 0) & (~g["gender"].str.lower().isin(["(not set)", "nan", "none", ""]))]
        if not g.empty:
            shown = True
            gcolors = {"male": C["blue"], "female": C["pink"]}
            fig = go.Figure(go.Pie(labels=g["gender"], values=g["sessions"], hole=0.66,
                                   marker=dict(colors=[gcolors.get(str(x).lower(), C["ink3"]) for x in g["gender"]],
                                               line=dict(color="#fff", width=2)),
                                   textinfo="none", sort=False,
                                   hovertemplate="%{label}<br>%{percent}<extra></extra>"))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=120,
                              margin=dict(l=0, r=0, t=8, b=0))
            st.markdown(f'<div style="font-size:10.5px;color:{C["ink3"]};font-weight:600;margin-top:6px;">GENDER</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    if not shown:
        st.info("حقول العمر/النوع غير متاحة في الـ connector.")
    st.markdown('</div>', unsafe_allow_html=True)

with r4[3]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Users by Day & Hour</div>', unsafe_allow_html=True)
    hr = pd.DataFrame()
    try:
        hr = scoped(load_dim(str(d_from), str(d_to), ["hour", "day_of_week"], ["sessions"], timeout=85))
    except Exception:
        hr = pd.DataFrame()
    if hr.empty or "hour" not in hr.columns:
        st.info("حقل الساعة غير متاح في الـ connector.")
    else:
        hr["hour"] = pd.to_numeric(hr["hour"], errors="coerce")
        hr = hr.dropna(subset=["hour"])
        hr["hour"] = hr["hour"].astype(int)
        pv = hr.groupby(["day_of_week", "hour"])["sessions"].sum().reset_index()
        order = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        short = {d: d[:3].title() for d in order}
        pt = pv.pivot(index="day_of_week", columns="hour", values="sessions").fillna(0)
        pt = pt.reindex([d for d in order if d in pt.index])
        fig = go.Figure(go.Heatmap(z=pt.values, x=[f"{h:02d}" for h in pt.columns],
                                   y=[short.get(d, str(d)[:3]) for d in pt.index],
                                   colorscale=[[0, "#EEF2FF"], [0.5, "#93B4FD"], [1, C["indigo"]]],
                                   showscale=False,
                                   hovertemplate="%{y} %{x}:00<br>%{z:,.0f}<extra></extra>"))
        fig.update_layout(**{k: v for k, v in PLOT.items() if k in ("paper_bgcolor", "plot_bgcolor", "font")},
                          height=210, margin=dict(l=4, r=4, t=6, b=4),
                          xaxis=dict(tickfont=dict(size=8)), yaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with r4[4]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-t">Alerts & Insights</div>', unsafe_allow_html=True)
    alerts = []
    if len(STAGES) >= 2:
        worst, wd = "", -1
        for i in range(1, len(STAGES)):
            drp = 100 - (STAGES[i][2] / STAGES[i-1][2] * 100 if STAGES[i-1][2] else 0)
            if drp > wd:
                wd, worst = drp, f"{STAGES[i-1][1]} → {STAGES[i][1]}"
        alerts.append(("High", C["red"], f"أعلى تسريب عند <b>{worst}</b> ({wd:.1f}%)"))
    d_cvr2 = pct_change(cvr, p_cvr)
    if d_cvr2 < -5:
        alerts.append(("High", C["red"], f"معدل التحويل نزل <b>{abs(d_cvr2):.1f}%</b>"))
    elif d_cvr2 > 5:
        alerts.append(("Low", C["green"], f"معدل التحويل زاد <b>{d_cvr2:.1f}%</b>"))
    d_rev2 = pct_change(t_rev, p_rev)
    alerts.append(("Medium" if abs(d_rev2) < 15 else "High",
                   C["green"] if d_rev2 >= 0 else C["red"],
                   f"الإيراد {'زاد' if d_rev2>=0 else 'نزل'} <b>{abs(d_rev2):.1f}%</b>"))
    if scope == "both" and not app_rows.empty and not web_rows.empty:
        w_c = (tot(web_rows,"transactions")/max(tot(web_rows,"sessions"),1))*100
        a_c = (tot(app_rows,"transactions")/max(tot(app_rows,"sessions"),1))*100
        if a_c < w_c * 0.8:
            alerts.append(("High", C["red"], f"تحويل التطبيق <b>{a_c:.2f}%</b> أقل من الويب <b>{w_c:.2f}%</b>"))
    d_u = pct_change(t_users, p_users)
    alerts.append(("Low", C["blue"], f"المستخدمون {'زادوا' if d_u>=0 else 'قلّوا'} <b>{abs(d_u):.1f}%</b>"))
    sev_bg = {"High": C["red_soft"], "Medium": C["amber_soft"], "Low": C["green_soft"]}
    sev_fg = {"High": C["red_dark"], "Medium": C["amber_dark"], "Low": C["green_dark"]}
    for sev, col, txt in alerts[:6]:
        st.markdown(f'<div class="alert-row"><span style="color:{col};font-size:13px;">●</span>'
                    f'<span style="flex:1">{txt}</span>'
                    f'<span class="badge" style="background:{sev_bg[sev]};color:{sev_fg[sev]}">{sev}</span></div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("💡 GA4 عبر Windsor.ai — Raneen.com (Website) + Raneen Mobile APP. "
           "الأقسام اللي حقولها غير متاحة في الـ connector بتظهر برسالة توضيحية.")
