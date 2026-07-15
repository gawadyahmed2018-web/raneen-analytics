"""
Raneen Google Ads Dashboard — page within the Analytics Hub.
Features:
- Account filter (Search / PMax / All)
- KPI cards with period-over-period comparison, arrows, and sparklines
- Performance split by campaign_type
- Full campaign table
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

from google_ads_windsor import (
    get_google_ads_data, safe_num, fmt_currency, fmt_number, fmt_pct,
    preset_to_range, previous_period,
)

st.set_page_config(page_title="Raneen Google Ads", page_icon="🔵", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.kpi-card { background: #FFFFFF; border: 1px solid #E2E6EA; border-radius: 12px; padding: 16px 18px; position: relative; overflow: hidden; margin-bottom: 10px; }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.kpi-label { font-size: 11px; color: #73726C; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.kpi-value { font-size: 24px; font-weight: 700; color: #1A1A2E; line-height: 1; margin-bottom: 4px; }
.kpi-delta { font-size: 12px; font-weight: 600; }
.kpi-delta-up { color: #1D9E75; }
.kpi-delta-down { color: #D85A30; }
.kpi-delta-flat { color: #888780; }
.section-header { display: flex; align-items: center; gap: 10px; padding: 6px 0 10px; border-bottom: 1px solid #E2E6EA; margin-bottom: 16px; margin-top: 8px; }
.section-dot { width: 8px; height: 8px; border-radius: 50%; }
.section-title { font-size: 15px; font-weight: 600; color: #1A1A2E; }
.styled-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.styled-table th { background: #F5F7FA; color: #73726C; font-weight: 500; font-size: 11px; text-transform: uppercase; padding: 10px 12px; border-bottom: 1px solid #E2E6EA; text-align: left; }
.styled-table td { padding: 10px 12px; border-bottom: 1px solid #F0F2F5; color: #1A1A2E; }
.styled-table tr:hover td { background: rgba(66,133,244,0.06); }
.badge { display: inline-block; font-size: 10px; padding: 3px 9px; border-radius: 10px; font-weight: 600; }
.badge-green { background: rgba(29,158,117,.2); color: #1D9E75; }
.badge-amber { background: rgba(239,159,39,.2); color: #EF9F27; }
.badge-red { background: rgba(216,90,48,.2); color: #D85A30; }
.badge-blue { background: rgba(66,133,244,.15); color: #4285F4; }
.badge-purple { background: rgba(127,119,221,.2); color: #7F77DD; }
</style>
""", unsafe_allow_html=True)

GOOGLE_BLUE = "#4285F4"
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#73726C", size=11),
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD"),
    yaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
)


def sparkline_svg(values, color=GOOGLE_BLUE, w=120, h=30):
    """Generate a tiny inline SVG sparkline from a list of numbers."""
    vals = [safe_num(v) for v in values]
    if not vals or max(vals) == min(vals):
        vals = vals or [0, 0]
        mn, mx = min(vals), max(vals) + 1
    else:
        mn, mx = min(vals), max(vals)
    n = len(vals)
    pts = []
    for i, v in enumerate(vals):
        x = (i / (n - 1)) * w if n > 1 else 0
        y = h - ((v - mn) / (mx - mn)) * h if mx > mn else h / 2
        pts.append(f"{x:.1f},{y:.1f}")
    points = " ".join(pts)
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block;margin-top:6px;">'
        f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def kpi_card_full(label, value, delta_pct, spark_values, accent=GOOGLE_BLUE, invert=False):
    """KPI card with value, period delta arrow, and sparkline.
    invert=True means lower is better (e.g. CPC, CPA)."""
    good = (delta_pct < 0) if invert else (delta_pct > 0)
    if abs(delta_pct) < 0.05:
        arrow, cls = "→", "kpi-delta-flat"
    elif good:
        arrow, cls = ("↓" if invert else "↑"), "kpi-delta-up"
    else:
        arrow, cls = ("↑" if invert else "↓"), "kpi-delta-down"
    spark = sparkline_svg(spark_values, color=accent)
    return (
        f'<div class="kpi-card"><div class="kpi-accent" style="background:{accent}"></div>'
        f'<div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>'
        f'<div class="kpi-delta {cls}">{arrow} {abs(delta_pct):.1f}% <span style="color:#9A9A8E;font-weight:400;">vs السابق</span></div>'
        f'{spark}</div>'
    )


def section_header(title, sub=""):
    return (
        f'<div class="section-header"><div class="section-dot" style="background:{GOOGLE_BLUE}"></div>'
        f'<div class="section-title">{title}</div>'
        f'{"<div style=" + chr(34) + "margin-left:auto;font-size:11px;color:#73726C" + chr(34) + ">" + sub + "</div>" if sub else ""}</div>'
    )


def pct_change(cur, prev):
    if prev == 0:
        return 0.0 if cur == 0 else 100.0
    return (cur - prev) / prev * 100


# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔵 Google Ads")
    st.caption("مصدر البيانات: Google Ads — عبر Windsor.ai")
    st.markdown("---")
    account_filter = st.radio(
        "Account",
        ["all", "search", "pmax"],
        format_func=lambda x: {"all": "🔵 All Accounts", "search": "🔍 Search", "pmax": "⚡ Performance Max"}.get(x, x),
    )
    st.markdown("---")
    date_preset = st.selectbox(
        "Date Range",
        ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month"],
        format_func=lambda x: {
            "last_7d": "Last 7 Days", "last_14d": "Last 14 Days", "last_30d": "Last 30 Days",
            "last_90d": "Last 90 Days", "this_month": "This Month", "last_month": "Last Month",
        }.get(x, x),
    )

# ── Header ───────────────────────────────────────────────
acc_label = {"all": "All Accounts", "search": "Search", "pmax": "Performance Max"}.get(account_filter, "")
st.markdown(f"""
<div style="padding:16px 0 12px; border-bottom:1px solid #E2E6EA; margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
  <div style="display:flex; align-items:center; gap:12px;">
    <span style="font-size:26px;">🔵</span>
    <div>
      <div style="font-size:22px; font-weight:800; color:#1A1A2E;">Raneen Google Ads — {acc_label}</div>
      <div style="font-size:11px; color:#9A9A8E;">Source: Google Ads via Windsor.ai</div>
    </div>
  </div>
  <div style="background:rgba(66,133,244,0.1); border:1px solid rgba(66,133,244,0.3); border-radius:20px; padding:4px 14px; font-size:11px; color:{GOOGLE_BLUE}; font-weight:600;">● Live · Google Ads</div>
</div>
""", unsafe_allow_html=True)

FIELDS = ["date", "account_name", "campaign", "campaign_type", "clicks", "spend", "impressions", "conversions", "conversions_value"]


@st.cache_data(ttl=300, show_spinner="Loading Google Ads data...")
def load_period(d_from, d_to):
    return get_google_ads_data(FIELDS, date_from=d_from, date_to=d_to)


d_from, d_to = preset_to_range(date_preset)
prev_from, prev_to = previous_period(d_from, d_to)

df_cur = load_period(str(d_from), str(d_to))
df_prev = load_period(prev_from, prev_to)

if df_cur.empty:
    st.warning("⚠️ لا توجد بيانات متاحة من Google Ads. تأكد من الاتصال على Windsor.ai.")
    if "_gads_errors" in st.session_state and st.session_state["_gads_errors"]:
        with st.expander("🔍 تفاصيل الخطأ"):
            st.write(st.session_state["_gads_errors"][-3:])
    st.stop()


# ── Normalize & filter by account ────────────────────────
def prep(df):
    if df.empty:
        return df
    for c in ["clicks", "spend", "impressions", "conversions", "conversions_value"]:
        if c in df.columns:
            df[c] = df[c].apply(safe_num)
    if account_filter == "search" and "campaign_type" in df.columns:
        df = df[df["campaign_type"].astype(str).str.upper() == "SEARCH"]
    elif account_filter == "pmax" and "campaign_type" in df.columns:
        df = df[df["campaign_type"].astype(str).str.upper() == "PERFORMANCE_MAX"]
    return df


df_cur = prep(df_cur.copy())
df_prev = prep(df_prev.copy())

if df_cur.empty:
    st.info(f"مفيش بيانات للفلتر '{acc_label}' في الفترة دي.")
    st.stop()


# ── Totals (current + previous) ──────────────────────────
def totals(df):
    return {
        "spend": df["spend"].sum() if "spend" in df else 0,
        "clicks": df["clicks"].sum() if "clicks" in df else 0,
        "impr": df["impressions"].sum() if "impressions" in df else 0,
        "conv": df["conversions"].sum() if "conversions" in df else 0,
        "conv_val": df["conversions_value"].sum() if "conversions_value" in df else 0,
    }


cur = totals(df_cur)
prev = totals(df_prev)

cur_roas = (cur["conv_val"] / cur["spend"]) if cur["spend"] > 0 else 0
prev_roas = (prev["conv_val"] / prev["spend"]) if prev["spend"] > 0 else 0
cur_cpa = (cur["spend"] / cur["conv"]) if cur["conv"] > 0 else 0
prev_cpa = (prev["spend"] / prev["conv"]) if prev["conv"] > 0 else 0
cur_cpc = (cur["spend"] / cur["clicks"]) if cur["clicks"] > 0 else 0
prev_cpc = (prev["spend"] / prev["clicks"]) if prev["clicks"] > 0 else 0
cur_ctr = (cur["clicks"] / cur["impr"] * 100) if cur["impr"] > 0 else 0
prev_ctr = (prev["clicks"] / prev["impr"] * 100) if prev["impr"] > 0 else 0


# ── Daily series for sparklines ──────────────────────────
def daily_series(df, col):
    if df.empty or "date" not in df.columns or col not in df.columns:
        return []
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"]).groupby("date")[col].sum().sort_index()
    return d.tolist()


sp_spend = daily_series(df_cur, "spend")
sp_conv = daily_series(df_cur, "conversions")
sp_cv = daily_series(df_cur, "conversions_value")
sp_clicks = daily_series(df_cur, "clicks")
sp_impr = daily_series(df_cur, "impressions")

# derived daily series for roas/cpa/cpc/ctr
d_cur = df_cur.copy()
d_cur["date"] = pd.to_datetime(d_cur["date"], errors="coerce")
daily = d_cur.dropna(subset=["date"]).groupby("date").sum(numeric_only=True).sort_index()
sp_roas = (daily["conversions_value"] / daily["spend"].replace(0, pd.NA)).fillna(0).tolist() if not daily.empty else []
sp_cpa = (daily["spend"] / daily["conversions"].replace(0, pd.NA)).fillna(0).tolist() if not daily.empty else []
sp_cpc = (daily["spend"] / daily["clicks"].replace(0, pd.NA)).fillna(0).tolist() if not daily.empty else []
sp_ctr = (daily["clicks"] / daily["impressions"].replace(0, pd.NA) * 100).fillna(0).tolist() if not daily.empty else []

# ── KPI Cards Row 1 ──────────────────────────────────────
st.markdown(section_header("Overview", f"{d_from} → {d_to} · مقارنة بالفترة السابقة"), unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(kpi_card_full("💰 Spend", fmt_currency(cur["spend"]), pct_change(cur["spend"], prev["spend"]), sp_spend, accent="#4285F4"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card_full("🎯 Conversions", fmt_number(cur["conv"]), pct_change(cur["conv"], prev["conv"]), sp_conv, accent="#1D9E75"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card_full("💵 Conv. Value", fmt_currency(cur["conv_val"]), pct_change(cur["conv_val"], prev["conv_val"]), sp_cv, accent="#1D9E75"), unsafe_allow_html=True)
with c4:
    st.markdown(kpi_card_full("📈 ROAS", f"{cur_roas:.2f}x", pct_change(cur_roas, prev_roas), sp_roas, accent="#7F77DD"), unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)
with c5:
    st.markdown(kpi_card_full("👁 Impressions", fmt_number(cur["impr"]), pct_change(cur["impr"], prev["impr"]), sp_impr, accent="#34A853"), unsafe_allow_html=True)
with c6:
    st.markdown(kpi_card_full("🖱 Clicks", fmt_number(cur["clicks"]), pct_change(cur["clicks"], prev["clicks"]), sp_clicks, accent="#34A853"), unsafe_allow_html=True)
with c7:
    st.markdown(kpi_card_full("💸 CPC", fmt_currency(cur_cpc, 2), pct_change(cur_cpc, prev_cpc), sp_cpc, accent="#EF9F27", invert=True), unsafe_allow_html=True)
with c8:
    st.markdown(kpi_card_full("🎯 CPA", fmt_currency(cur_cpa, 0) if cur["conv"] else "—", pct_change(cur_cpa, prev_cpa), sp_cpa, accent="#EF9F27", invert=True), unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Performance by campaign_type (only in "all" view) ────
if account_filter == "all" and "campaign_type" in df_cur.columns:
    st.markdown(section_header("Performance by Type", "Search vs PMax vs غيره"), unsafe_allow_html=True)
    by_type = df_cur.groupby("campaign_type", as_index=False).sum(numeric_only=True)
    by_type["roas"] = by_type.apply(lambda r: r["conversions_value"] / r["spend"] if r["spend"] > 0 else 0, axis=1)
    by_type = by_type.sort_values("spend", ascending=False)

    cols = st.columns(len(by_type)) if len(by_type) else [st]
    type_colors = {"SEARCH": "#4285F4", "PERFORMANCE_MAX": "#7F77DD", "DEMAND_GEN": "#EF9F27", "MULTI_CHANNEL": "#34A853"}
    type_labels = {"SEARCH": "🔍 Search", "PERFORMANCE_MAX": "⚡ PMax", "DEMAND_GEN": "📢 Demand Gen", "MULTI_CHANNEL": "📱 App/Multi"}
    for col, (_, r) in zip(cols, by_type.iterrows()):
        t = r["campaign_type"]
        with col:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-accent" style="background:{type_colors.get(t,"#888")}"></div>'
                f'<div class="kpi-label">{type_labels.get(t, t)}</div>'
                f'<div class="kpi-value">{fmt_currency(r["spend"])}</div>'
                f'<div style="font-size:12px;color:#73726C;margin-top:4px;">ROAS {r["roas"]:.2f}x · {fmt_number(r["conversions"])} conv</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Trends ───────────────────────────────────────────────
if "date" in df_cur.columns:
    df_ts = df_cur.copy()
    df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
    df_ts = df_ts.dropna(subset=["date"]).groupby("date", as_index=False).sum(numeric_only=True).sort_values("date")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section_header("Spend vs Conversions"), unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_ts["date"], y=df_ts["spend"], name="Spend", marker_color="#4285F4", opacity=0.75))
        fig.add_trace(go.Scatter(x=df_ts["date"], y=df_ts["conversions"], name="Conv", mode="lines+markers", line=dict(color="#1D9E75", width=2), yaxis="y2"))
        fig.update_layout(**PLOT_LAYOUT, height=280, yaxis2=dict(overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.markdown(section_header("Conversion Value Over Time"), unsafe_allow_html=True)
        fig2 = px.area(df_ts, x="date", y="conversions_value", color_discrete_sequence=["#1D9E75"])
        fig2.update_traces(fill="tozeroy", fillcolor="rgba(29,158,117,0.15)")
        fig2.update_layout(**PLOT_LAYOUT, height=280)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Campaign table ───────────────────────────────────────
st.markdown(section_header("Campaign Performance", "Full breakdown"), unsafe_allow_html=True)
df_camp = df_cur.groupby(["campaign", "campaign_type"], as_index=False).sum(numeric_only=True) if "campaign_type" in df_cur.columns else df_cur.groupby("campaign", as_index=False).sum(numeric_only=True)
df_camp = df_camp[df_camp["spend"] > 0].copy()
df_camp["roas"] = df_camp.apply(lambda r: r["conversions_value"] / r["spend"] if r["spend"] > 0 else 0, axis=1)
df_camp["cpa"] = df_camp.apply(lambda r: r["spend"] / r["conversions"] if r["conversions"] > 0 else 0, axis=1)
df_camp = df_camp.sort_values("spend", ascending=False)

type_badge = {"SEARCH": "badge-blue", "PERFORMANCE_MAX": "badge-purple", "DEMAND_GEN": "badge-amber", "MULTI_CHANNEL": "badge-green"}
rows = []
for _, r in df_camp.head(50).iterrows():
    rr = r["roas"]
    badge = '<span class="badge badge-green">قوي</span>' if rr >= 3 else ('<span class="badge badge-amber">متوسط</span>' if rr >= 1 else '<span class="badge badge-red">ضعيف</span>')
    tb = ""
    if "campaign_type" in df_camp.columns:
        t = r["campaign_type"]
        tb = f'<span class="badge {type_badge.get(t,"badge-blue")}">{t.replace("PERFORMANCE_MAX","PMax").replace("MULTI_CHANNEL","App").title()}</span>'
    rows.append(
        f"<tr><td style='font-size:12px'>{r['campaign']}</td>"
        f"<td>{tb}</td>"
        f"<td>{fmt_currency(r['spend'])}</td>"
        f"<td>{fmt_number(r['clicks'])}</td>"
        f"<td>{r['conversions']:.1f}</td>"
        f"<td>{fmt_currency(r['conversions_value'])}</td>"
        f"<td>{rr:.2f}x</td>"
        f"<td>{fmt_currency(r['cpa'],0) if r['conversions']>0 else '—'}</td>"
        f"<td>{badge}</td></tr>"
    )
st.markdown(
    "<table class='styled-table'><thead><tr><th>Campaign</th><th>Type</th><th>Spend</th><th>Clicks</th>"
    "<th>Conv.</th><th>Conv. Value</th><th>ROAS</th><th>CPA</th><th>Rating</th></tr></thead>"
    f"<tbody>{''.join(rows)}</tbody></table>",
    unsafe_allow_html=True,
)

import io
buf = io.BytesIO()
df_camp.to_csv(buf, index=False, encoding="utf-8-sig")
st.download_button("📥 Export CSV", buf.getvalue(), "google_ads_campaigns.csv", "text/csv")
