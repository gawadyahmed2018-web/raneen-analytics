"""
Executive Summary — the top-level profitability view for the Analytics Hub.
Source: "Target & Sales Overview" Google Sheet (live via published CSV).
Shows spending breakdown, sales (Retail vs Marketplace), and Actual vs Target.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

from sheets_connector import load_sales_sheet, safe_num, fmt_egp, fmt_number, fmt_pct

st.set_page_config(page_title="Executive Summary", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans Arabic', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1400px; }
.kpi-card { background: #FFFFFF; border: 1px solid #E2E6EA; border-radius: 14px; padding: 18px 20px; position: relative; overflow: hidden; margin-bottom: 12px; }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.kpi-label { font-size: 11px; color: #73726C; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #1A1A2E; line-height: 1; margin-bottom: 6px; }
.kpi-sub { font-size: 12px; color: #73726C; }
.target-bar-bg { background: #F0F2F5; border-radius: 6px; height: 8px; margin-top: 8px; overflow: hidden; }
.target-bar-fill { height: 100%; border-radius: 6px; }
.target-label { font-size: 11px; color: #9A9A8E; margin-top: 4px; }
.section-header { display: flex; align-items: center; gap: 10px; padding: 6px 0 10px; border-bottom: 1px solid #E2E6EA; margin-bottom: 16px; margin-top: 8px; }
.section-dot { width: 8px; height: 8px; border-radius: 50%; }
.section-title { font-size: 15px; font-weight: 600; color: #1A1A2E; }
.bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.bar-name { font-size: 12px; color: #73726C; min-width: 130px; }
.bar-track { flex: 1; height: 10px; background: #F0F2F5; border-radius: 5px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 5px; }
.bar-val { font-size: 12px; color: #1A1A2E; min-width: 90px; text-align: right; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

ACCENT = "#2A3050"
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans Arabic", color="#73726C", size=11),
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD"),
    yaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
)


def kpi_with_target(label, actual, target, accent="#3266AD", is_spend=False):
    pct = (actual / target * 100) if target else 0
    if is_spend:
        # For spending, under target is good (green), over is warning
        color = "#1D9E75" if pct <= 100 else "#EF9F27" if pct <= 110 else "#D85A30"
    else:
        color = "#1D9E75" if pct >= 100 else "#EF9F27" if pct >= 85 else "#D85A30"
    bar_w = min(pct, 100)
    return (
        f'<div class="kpi-card"><div class="kpi-accent" style="background:{accent}"></div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{fmt_egp(actual)}</div>'
        f'<div class="target-bar-bg"><div class="target-bar-fill" style="width:{bar_w}%;background:{color}"></div></div>'
        f'<div class="target-label">Target: {fmt_egp(target)} · <b style="color:{color}">{pct:.0f}%</b></div>'
        f'</div>'
    )


def section_header(title, sub=""):
    return (
        f'<div class="section-header"><div class="section-dot" style="background:{ACCENT}"></div>'
        f'<div class="section-title">{title}</div>'
        f'{"<div style=" + chr(34) + "margin-left:auto;font-size:11px;color:#73726C" + chr(34) + ">" + sub + "</div>" if sub else ""}</div>'
    )


def bar_html(name, pct, color, val_str):
    return (
        f'<div class="bar-row"><div class="bar-name">{name}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{max(pct,1)}%;background:{color}"></div></div>'
        f'<div class="bar-val">{val_str}</div></div>'
    )


# ── Load ─────────────────────────────────────────────────
df = load_sales_sheet()

if df.empty:
    st.error("❌ تعذّر تحميل الشيت. تأكد إن الـ Google Sheet منشور (Publish to web).")
    if "_sheet_errors" in st.session_state:
        with st.expander("تفاصيل الخطأ"):
            st.write(st.session_state["_sheet_errors"][-3:])
    st.stop()

# Only rows with actual sales data
df_valid = df[df["Date"].notna() & df["Confirmed Sales"].notna() & (df["Confirmed Sales"] != 0)].copy()

# ── Sidebar ──────────────────────────────────────────────
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
    min_date = df_valid["Date"].min()

    if period == "custom":
        c_from = st.date_input("من", max_date - timedelta(days=30))
        c_to = st.date_input("إلى", max_date)

# ── Resolve period ───────────────────────────────────────
def get_period_df(df_valid, period):
    max_d = df_valid["Date"].max()
    if period == "last_7d":
        start = max_d - timedelta(days=6)
        return df_valid[df_valid["Date"] >= start]
    elif period == "last_30d":
        start = max_d - timedelta(days=29)
        return df_valid[df_valid["Date"] >= start]
    elif period == "last_90d":
        start = max_d - timedelta(days=89)
        return df_valid[df_valid["Date"] >= start]
    elif period == "this_month":
        return df_valid[(df_valid["Date"].dt.month == max_d.month) & (df_valid["Date"].dt.year == max_d.year)]
    elif period == "last_month":
        prev = (max_d.replace(day=1) - timedelta(days=1))
        return df_valid[(df_valid["Date"].dt.month == prev.month) & (df_valid["Date"].dt.year == prev.year)]
    elif period == "all_time":
        return df_valid
    elif period == "custom":
        return df_valid[(df_valid["Date"].dt.date >= c_from) & (df_valid["Date"].dt.date <= c_to)]
    return df_valid


d = get_period_df(df_valid, period)

# ── Header ───────────────────────────────────────────────
p_from = d["Date"].min().date() if not d.empty else "—"
p_to = d["Date"].max().date() if not d.empty else "—"
st.markdown(f"""
<div style="padding:14px 0 20px; border-bottom:1px solid #E2E6EA; margin-bottom:24px; display:flex; align-items:center; justify-content:space-between;">
  <div style="display:flex; align-items:center; gap:14px;">
    <span style="font-size:34px;">🎯</span>
    <div>
      <div style="font-size:24px; font-weight:800; color:#1A1A2E;">Executive Summary</div>
      <div style="font-size:12px; color:#9A9A8E;">{p_from} → {p_to} · الربحية والأداء مقابل التارجت</div>
    </div>
  </div>
  <div style="background:rgba(29,158,117,0.1); border:1px solid rgba(29,158,117,0.3); border-radius:20px; padding:4px 14px; font-size:11px; color:#1D9E75; font-weight:600;">● Live · Google Sheet</div>
</div>
""", unsafe_allow_html=True)

if d.empty:
    st.info("مفيش بيانات في الفترة المختارة.")
    st.stop()

# ── Aggregate ────────────────────────────────────────────
def s(col):
    return d[col].sum() if col in d.columns else 0

total_spend = s("Total Spending")
spend_target = s("Spending Target")
conf_sales = s("Confirmed Sales")
conf_target = s("Confirmed Target")
recv_sales = s("Received Sales")
recv_target = s("Received Target")
retail_sales = s("Retail Confirmed Sales")
retail_target = s("Retail Confirmed Target")
mp_sales = s("Marketplace Confirmed Sales")
mp_target = s("Marketplace Confirmed Target")
orders = s("No. of Orders")

fb = s("Facebook Spending")
google = s("Google Spending")
tiktok = s("TikTok Spending")
sms = s("SMS Spending")
criteo = s("Criteo Spending")
coupons = s("Coupons")
extra = s("Extra Spending")

blended_roas = (conf_sales / total_spend) if total_spend else 0
aov = (conf_sales / orders) if orders else 0
confirm_rate = (conf_sales / recv_sales * 100) if recv_sales else 0

# ── Top KPIs with targets ────────────────────────────────
st.markdown(section_header("الأداء مقابل التارجت", "Actual vs Target"), unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(kpi_with_target("💰 Confirmed Sales", conf_sales, conf_target, accent="#1D9E75"), unsafe_allow_html=True)
with c2: st.markdown(kpi_with_target("💸 Total Spending", total_spend, spend_target, accent="#D85A30", is_spend=True), unsafe_allow_html=True)
with c3: st.markdown(kpi_with_target("🏪 Retail Sales", retail_sales, retail_target, accent="#3266AD"), unsafe_allow_html=True)
with c4: st.markdown(kpi_with_target("🛒 Marketplace Sales", mp_sales, mp_target, accent="#7F77DD"), unsafe_allow_html=True)

# ── Secondary KPIs ───────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-accent" style="background:#7F77DD"></div><div class="kpi-label">📈 Blended ROAS</div><div class="kpi-value">{blended_roas:.1f}x</div><div class="kpi-sub">مبيعات ÷ إجمالي الصرف</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-accent" style="background:#3266AD"></div><div class="kpi-label">📦 Orders</div><div class="kpi-value">{fmt_number(orders)}</div><div class="kpi-sub">عدد الأوردرات</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-accent" style="background:#1D9E75"></div><div class="kpi-label">🧾 AOV</div><div class="kpi-value">{fmt_egp(aov,0)}</div><div class="kpi-sub">متوسط قيمة الطلب</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-accent" style="background:#EF9F27"></div><div class="kpi-label">✅ Confirmation Rate</div><div class="kpi-value">{confirm_rate:.1f}%</div><div class="kpi-sub">Confirmed ÷ Received</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Spending breakdown + Sales split ─────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.markdown(section_header("توزيع الصرف", "Spending Breakdown"), unsafe_allow_html=True)
    spend_items = [
        ("💙 Facebook", fb, "#1877F2"),
        ("🔵 Google", google, "#4285F4"),
        ("🎟️ Coupons", coupons, "#EF9F27"),
        ("⚫ TikTok", tiktok, "#1A1A2E"),
        ("📱 SMS", sms, "#1D9E75"),
        ("🟣 Criteo", criteo, "#7F77DD"),
        ("➕ Extra", extra, "#888780"),
    ]
    spend_items = [(n, v, c) for n, v, c in spend_items if v > 0]
    spend_items.sort(key=lambda x: x[1], reverse=True)
    mx = max([v for _, v, _ in spend_items]) if spend_items else 1
    for name, val, color in spend_items:
        pct_of_total = (val / total_spend * 100) if total_spend else 0
        st.markdown(bar_html(name, val / mx * 100, color, f"{fmt_egp(val)} ({pct_of_total:.0f}%)"), unsafe_allow_html=True)

with col_r:
    st.markdown(section_header("Retail vs Marketplace", "توزيع المبيعات المؤكدة"), unsafe_allow_html=True)
    fig = go.Figure(go.Pie(
        labels=["Retail", "Marketplace"],
        values=[retail_sales, mp_sales],
        marker_colors=["#3266AD", "#7F77DD"],
        hole=0.6, textinfo="label+percent", textfont_size=13,
    ))
    fig.update_layout(**PLOT_LAYOUT, height=260, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Trends over time ─────────────────────────────────────
st.markdown(section_header("الاتجاه اليومي", "Sales vs Spending Over Time"), unsafe_allow_html=True)
d_ts = d.sort_values("Date")

fig2 = go.Figure()
fig2.add_trace(go.Bar(x=d_ts["Date"], y=d_ts["Total Spending"], name="Spending", marker_color="rgba(216,90,48,0.7)"))
fig2.add_trace(go.Scatter(x=d_ts["Date"], y=d_ts["Confirmed Sales"], name="Confirmed Sales", mode="lines", line=dict(color="#1D9E75", width=2), yaxis="y2"))
fig2.update_layout(**PLOT_LAYOUT, height=300, yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Sales"))
st.plotly_chart(fig2, use_container_width=True)

# ── Sales funnel: Received → Confirmed ───────────────────
st.markdown(section_header("مسار المبيعات", "Received → Confirmed"), unsafe_allow_html=True)
fc1, fc2, fc3 = st.columns(3)
with fc1:
    st.markdown(kpi_with_target("📥 Received Sales", recv_sales, recv_target, accent="#EF9F27"), unsafe_allow_html=True)
with fc2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-accent" style="background:#1D9E75"></div><div class="kpi-label">✅ Confirmed Sales</div><div class="kpi-value">{fmt_egp(conf_sales)}</div><div class="kpi-sub">{confirm_rate:.1f}% confirmation rate</div></div>', unsafe_allow_html=True)
with fc3:
    lost = recv_sales - conf_sales
    lost_pct = (lost / recv_sales * 100) if recv_sales else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-accent" style="background:#D85A30"></div><div class="kpi-label">❌ Not Confirmed</div><div class="kpi-value">{fmt_egp(lost)}</div><div class="kpi-sub">{lost_pct:.1f}% من المستلم</div></div>', unsafe_allow_html=True)

# ── Export ───────────────────────────────────────────────
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
import io
buf = io.BytesIO()
d.to_csv(buf, index=False, encoding="utf-8-sig")
st.download_button("📥 Export Period Data", buf.getvalue(), "executive_summary.csv", "text/csv")

st.caption("💡 البيانات حيّة من Google Sheet — أي تحديث في الشيت يظهر هنا خلال 5 دقائق (بعد انتهاء الـ cache).")
