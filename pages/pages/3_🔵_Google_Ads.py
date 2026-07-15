"""
Raneen Google Ads Dashboard — page within the Analytics Hub.
Pulls directly from the Google Ads connector on Windsor.ai.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

from google_ads_windsor import get_google_ads_data, safe_num, fmt_currency, fmt_number, fmt_pct

st.set_page_config(page_title="Raneen Google Ads", page_icon="🔵", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.kpi-card { background: #FFFFFF; border: 1px solid #E2E6EA; border-radius: 12px; padding: 18px 20px; position: relative; overflow: hidden; margin-bottom: 10px; }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.kpi-label { font-size: 11px; color: #73726C; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #1A1A2E; line-height: 1; margin-bottom: 6px; }
.kpi-sub { font-size: 12px; color: #73726C; }
.section-header { display: flex; align-items: center; gap: 10px; padding: 6px 0 10px; border-bottom: 1px solid #E2E6EA; margin-bottom: 16px; }
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
</style>
""", unsafe_allow_html=True)

GOOGLE_BLUE = "#4285F4"
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans Arabic", color="#73726C", size=11),
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD"),
    yaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
)


def kpi_card(label, value, sub="", accent=GOOGLE_BLUE):
    return (
        f'<div class="kpi-card"><div class="kpi-accent" style="background:{accent}"></div>'
        f'<div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div></div>'
    )


def section_header(title, sub=""):
    return (
        f'<div class="section-header"><div class="section-dot" style="background:{GOOGLE_BLUE}"></div>'
        f'<div class="section-title">{title}</div>'
        f'{"<div style=" + chr(34) + "margin-left:auto;font-size:11px;color:#73726C" + chr(34) + ">" + sub + "</div>" if sub else ""}</div>'
    )


# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔵 Google Ads")
    st.caption("مصدر البيانات: Google Ads — عبر Windsor.ai")
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
st.markdown(f"""
<div style="padding:16px 0 12px; border-bottom:1px solid #E2E6EA; margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
  <div style="display:flex; align-items:center; gap:12px;">
    <span style="font-size:26px;">🔵</span>
    <div>
      <div style="font-size:22px; font-weight:800; color:#1A1A2E;">Raneen Google Ads</div>
      <div style="font-size:11px; color:#9A9A8E;">Source: Google Ads via Windsor.ai</div>
    </div>
  </div>
  <div style="background:rgba(66,133,244,0.1); border:1px solid rgba(66,133,244,0.3); border-radius:20px; padding:4px 14px; font-size:11px; color:{GOOGLE_BLUE}; font-weight:600;">● Live · Google Ads</div>
</div>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner="Loading Google Ads data...")
def load_gads(preset):
    return get_google_ads_data(
        ["date", "campaign", "clicks", "spend", "impressions", "conversions", "conversions_value"],
        preset,
    )


df = load_gads(date_preset)

if df.empty:
    st.warning("⚠️ لا توجد بيانات متاحة من Google Ads. تأكد من الاتصال على Windsor.ai.")
    if "_gads_errors" in st.session_state and st.session_state["_gads_errors"]:
        with st.expander("🔍 تفاصيل الخطأ"):
            st.write(st.session_state["_gads_errors"][-3:])
    st.stop()

# ── Normalize ────────────────────────────────────────────
for c in ["clicks", "spend", "impressions", "conversions", "conversions_value"]:
    if c in df.columns:
        df[c] = df[c].apply(safe_num)

# ── Totals ───────────────────────────────────────────────
tot_spend = df["spend"].sum()
tot_clicks = df["clicks"].sum()
tot_impr = df["impressions"].sum()
tot_conv = df["conversions"].sum()
tot_conv_val = df["conversions_value"].sum()

ctr = (tot_clicks / tot_impr * 100) if tot_impr > 0 else 0
cpc = (tot_spend / tot_clicks) if tot_clicks > 0 else 0
cpa = (tot_spend / tot_conv) if tot_conv > 0 else 0
roas = (tot_conv_val / tot_spend) if tot_spend > 0 else 0
conv_rate = (tot_conv / tot_clicks * 100) if tot_clicks > 0 else 0

# ── KPIs ─────────────────────────────────────────────────
st.markdown(section_header("Overview", "Google Ads Performance"), unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(kpi_card("💰 Total Spend", fmt_currency(tot_spend), "Ad spend", accent="#4285F4"), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("🎯 Conversions", fmt_number(tot_conv), f"Conv rate: {conv_rate:.2f}%", accent="#1D9E75"), unsafe_allow_html=True)
with c3: st.markdown(kpi_card("💵 Conv. Value", fmt_currency(tot_conv_val), "Revenue attributed", accent="#1D9E75"), unsafe_allow_html=True)
with c4: st.markdown(kpi_card("📈 ROAS", f"{roas:.2f}x" if roas else "—", "Value / Spend", accent="#7F77DD"), unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
c5, c6, c7, c8 = st.columns(4)
with c5: st.markdown(kpi_card("👁 Impressions", fmt_number(tot_impr), "Total shown", accent="#34A853"), unsafe_allow_html=True)
with c6: st.markdown(kpi_card("🖱 Clicks", fmt_number(tot_clicks), f"CTR: {ctr:.2f}%", accent="#34A853"), unsafe_allow_html=True)
with c7: st.markdown(kpi_card("💸 CPC", fmt_currency(cpc, 2), "Cost per click", accent="#EF9F27"), unsafe_allow_html=True)
with c8: st.markdown(kpi_card("🎯 CPA", fmt_currency(cpa, 0) if tot_conv else "—", "Cost per conversion", accent="#EF9F27"), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Trends ───────────────────────────────────────────────
if "date" in df.columns:
    df_ts = df.copy()
    df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
    df_ts = df_ts.dropna(subset=["date"]).groupby("date", as_index=False).sum(numeric_only=True).sort_values("date")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section_header("Spend vs Conversions"), unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_ts["date"], y=df_ts["spend"], name="Spend", marker_color="#4285F4", opacity=0.75))
        fig.add_trace(go.Scatter(x=df_ts["date"], y=df_ts["conversions"], name="Conversions", mode="lines+markers", line=dict(color="#1D9E75", width=2), yaxis="y2"))
        fig.update_layout(**PLOT_LAYOUT, height=280, yaxis2=dict(overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.markdown(section_header("Conversion Value Over Time"), unsafe_allow_html=True)
        fig2 = px.area(df_ts, x="date", y="conversions_value", color_discrete_sequence=["#1D9E75"])
        fig2.update_traces(fill="tozeroy", fillcolor="rgba(29,158,117,0.15)")
        fig2.update_layout(**PLOT_LAYOUT, height=280)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Campaign table ───────────────────────────────────────
st.markdown(section_header("Campaign Performance", "Full breakdown"), unsafe_allow_html=True)
df_camp = df.groupby("campaign", as_index=False).sum(numeric_only=True)
df_camp = df_camp[df_camp["spend"] > 0].copy()
df_camp["roas"] = df_camp.apply(lambda r: r["conversions_value"] / r["spend"] if r["spend"] > 0 else 0, axis=1)
df_camp["cpa"] = df_camp.apply(lambda r: r["spend"] / r["conversions"] if r["conversions"] > 0 else 0, axis=1)
df_camp = df_camp.sort_values("spend", ascending=False)

rows = []
for _, r in df_camp.head(40).iterrows():
    rr = r["roas"]
    badge = '<span class="badge badge-green">قوي</span>' if rr >= 3 else ('<span class="badge badge-amber">متوسط</span>' if rr >= 1 else '<span class="badge badge-red">ضعيف</span>')
    rows.append(
        f"<tr><td style='font-size:12px'>{r['campaign']}</td>"
        f"<td>{fmt_currency(r['spend'])}</td>"
        f"<td>{fmt_number(r['clicks'])}</td>"
        f"<td>{fmt_number(r['impressions'])}</td>"
        f"<td>{r['conversions']:.1f}</td>"
        f"<td>{fmt_currency(r['conversions_value'])}</td>"
        f"<td>{rr:.2f}x</td>"
        f"<td>{fmt_currency(r['cpa'],0) if r['conversions']>0 else '—'}</td>"
        f"<td>{badge}</td></tr>"
    )
st.markdown(
    "<table class='styled-table'><thead><tr><th>Campaign</th><th>Spend</th><th>Clicks</th><th>Impressions</th>"
    "<th>Conv.</th><th>Conv. Value</th><th>ROAS</th><th>CPA</th><th>Rating</th></tr></thead>"
    f"<tbody>{''.join(rows)}</tbody></table>",
    unsafe_allow_html=True,
)

import io
buf = io.BytesIO()
df_camp.to_csv(buf, index=False, encoding="utf-8-sig")
st.download_button("📥 Export CSV", buf.getvalue(), "google_ads_campaigns.csv", "text/csv")

# ── Top/bottom performers ────────────────────────────────
if len(df_camp) >= 2:
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    col_t, col_b = st.columns(2)
    with col_t:
        st.markdown(section_header("🏆 Best ROAS"), unsafe_allow_html=True)
        best = df_camp.sort_values("roas", ascending=False).head(6)
        fig_b = px.bar(best, x="roas", y="campaign", orientation="h", color_discrete_sequence=["#1D9E75"])
        fig_b.update_layout(**PLOT_LAYOUT, height=240, showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)
    with col_b:
        st.markdown(section_header("⚠️ Needs Review", "Lowest ROAS with spend"), unsafe_allow_html=True)
        worst = df_camp[df_camp["spend"] > df_camp["spend"].median()].sort_values("roas").head(6)
        fig_w = px.bar(worst, x="roas", y="campaign", orientation="h", color_discrete_sequence=["#D85A30"])
        fig_w.update_layout(**PLOT_LAYOUT, height=240, showlegend=False)
        st.plotly_chart(fig_w, use_container_width=True)
