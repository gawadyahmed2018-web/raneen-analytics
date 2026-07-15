"""
Raneen Meta Ads Dashboard — Standalone
Pulls directly from Meta (Facebook/Instagram) Ads via Windsor.ai.
Numbers here are sourced from Meta itself — NOT GA4 — so they should
match Meta Ads Manager (Spend, Purchases, ROAS) almost exactly.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

from meta_windsor import get_meta_data, safe_num, fmt_currency, fmt_number, fmt_pct

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(page_title="Raneen Meta Ads", page_icon="📣", layout="wide", initial_sidebar_state="expanded")

# ─────────────────────────────────────────────
# CSS — same visual language as raneen-analytics, Meta-blue accent
# ─────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: #0A0F1C;
    color: #E2E8F0 !important;
}
.kpi-card { background: #111827; border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; padding: 18px 22px; margin-bottom: 10px; }
.kpi-accent { height: 3px; border-radius: 12px 12px 0 0; margin: -18px -22px 14px -22px; }
.kpi-label { font-size: 11px; color: #94A3B8 !important; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600; }
.kpi-value { font-family: 'Courier New', Courier, monospace; font-size: 28px; font-weight: 800; color: #FFFFFF !important; }
.kpi-sub { font-size: 12px; color: #CBD5E1 !important; margin-top: 4px; }
[data-testid="stMetricValue"] { font-family: 'Courier New', Courier, monospace !important; color: #FFFFFF !important; }
.styled-table { width: 100%; border-collapse: collapse; font-size: 13px; background: #0F1623; }
.styled-table th { background: #1A2332 !important; color: #94A3B8 !important; font-weight: 700; font-size: 11px; text-transform: uppercase; padding: 12px 14px; border-bottom: 2px solid rgba(255,255,255,0.12); text-align: left; }
.styled-table td { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.06); color: #F1F5F9 !important; font-weight: 500; }
.styled-table tr:nth-child(even) td { background: #131B29 !important; }
.styled-table tr:nth-child(odd) td { background: #0F1623 !important; }
.styled-table tr:hover td { background: rgba(24,119,242,0.15) !important; }
.badge { display: inline-block; font-size: 10px; padding: 3px 9px; border-radius: 10px; font-weight: 600; }
.badge-green { background: rgba(29,158,117,0.2); color: #1D9E75; }
.badge-amber { background: rgba(239,159,39,0.2); color: #EF9F27; }
.badge-red   { background: rgba(216,90,48,0.2); color: #D85A30; }
.section-header { display: flex; align-items: center; gap: 10px; padding: 6px 0 10px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px; }
.section-title { font-size: 15px; font-weight: 700; color: #F1F5F9; }
.section-dot { width: 8px; height: 8px; border-radius: 50%; }
</style>
""", unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="Courier New, monospace", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, zeroline=False, color="#475569"),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, color="#475569"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
)
META_BLUE = "#1877F2"


def kpi_card(label, value, sub="", accent="#1877F2"):
    return (
        f'<div class="kpi-card"><div class="kpi-accent" style="background:{accent}"></div>'
        f'<div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div></div>'
    )


def section_header(title, sub="", color=META_BLUE):
    return (
        f'<div class="section-header"><div class="section-dot" style="background:{color}"></div>'
        f'<div class="section-title">{title}</div>'
        f'{"<div style=" + chr(34) + "margin-left:auto;font-size:11px;color:#64748B" + chr(34) + ">" + sub + "</div>" if sub else ""}</div>'
    )


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📣 Raneen Meta Ads")
    st.caption("مصدر البيانات: Meta (Facebook/Instagram) مباشرة — عبر Windsor.ai")
    st.markdown("---")

    date_preset = st.selectbox(
        "Date Range",
        ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month", "custom"],
        format_func=lambda x: {
            "last_7d": "Last 7 Days", "last_14d": "Last 14 Days", "last_30d": "Last 30 Days",
            "last_90d": "Last 90 Days", "this_month": "This Month", "last_month": "Last Month",
            "custom": "Custom Range",
        }.get(x, x),
    )
    if date_preset == "custom":
        custom_from = st.date_input("From", date.today() - timedelta(days=30))
        custom_to = st.date_input("To", date.today() - timedelta(days=1))

    st.markdown("---")
    level_label = st.radio("Reporting Level", ["Campaign", "Ad Set", "Ad"])
    # Map UI label -> actual Windsor/Facebook field name.
    # Confirmed via live API error: "adset"/"ad" are NOT valid field names —
    # Facebook requires "adset_name" / "ad_name" (campaign stays as "campaign").
    LEVEL_FIELD_MAP = {"Campaign": "campaign", "Ad Set": "adset_name", "Ad": "ad_name"}
    level = LEVEL_FIELD_MAP[level_label]
    if level_label in ("Ad Set", "Ad"):
        st.caption(f"⏳ مستوى {level_label} فيه بيانات أكتر تفصيلاً — التحميل ممكن ياخد لحد دقيقة.")

    st.markdown("---")
    st.caption("⚠️ هذه الأرقام مصدرها Meta مباشرة — لو شايف فرق بينها وبين GA4 dashboard، ده طبيعي ومتوقع (راجع شرح الفجوة).")

_d_from, _d_to = (str(custom_from), str(custom_to)) if date_preset == "custom" else (None, None)

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="padding:16px 0 12px; border-bottom:1px solid rgba(255,255,255,0.07); margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div style="font-size:28px;">📣</div>
    <div>
      <div style="font-size:22px; font-weight:800;">Raneen Meta Ads Dashboard</div>
      <div style="font-size:11px; color:#475569; margin-top:2px;">Source of truth: Meta Ads Manager (via Windsor.ai)</div>
    </div>
  </div>
  <div style="background:rgba(24,119,242,0.12); border:1px solid rgba(24,119,242,0.3); border-radius:20px; padding:4px 14px; font-size:11px; color:{META_BLUE}; font-weight:600;">
    ● Live via Windsor · Meta
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Load campaign-level data
# Field names confirmed live against the actual Windsor/Facebook API.
# "purchase_roas", "roas", "purchases", "purchase_value" do NOT exist as
# fields on this connector (confirmed via a live 400 error response) — only
# actions_purchase / action_values_purchase are real. ROAS, CPA, etc. are
# all computed manually below from spend + these two fields.
# ─────────────────────────────────────────────
BASE_FIELDS = ["date", "account_name", "campaign", "spend", "clicks", "impressions", "reach", "frequency"]
ACTION_FIELDS = ["actions_purchase", "action_values_purchase"]


@st.cache_data(ttl=300, show_spinner="Loading Meta Ads data... قد يستغرق دقيقة في مستوى Ad Set / Ad")
def load_meta_campaigns(preset, d_from, d_to, lvl):
    field_set = list(dict.fromkeys(BASE_FIELDS + [lvl] + ACTION_FIELDS))
    # Ad Set and Ad level return far more rows than Campaign level —
    # Meta's API takes noticeably longer to aggregate and return them.
    req_timeout = 120 if lvl in ("adset_name", "ad_name") else 60
    df = get_meta_data(field_set, preset, d_from, d_to, timeout=req_timeout)
    return df, False  # second value kept for compatibility with the rest of the app


df_meta, used_fallback = load_meta_campaigns(date_preset, _d_from, _d_to, level)

# ─────────────────────────────────────────────
# Guard (empty check first — normalization needs columns to exist)
# ─────────────────────────────────────────────
if df_meta.empty:
    with st.expander("🔍 Debug — البيانات الراجعة من Windsor (تأكد من الـ field names)"):
        st.error("لم ترجع أي بيانات من Windsor. تحقق من الـ API key أو من وجود بيانات في الفترة المختارة.")
        if "_meta_api_errors" in st.session_state and st.session_state["_meta_api_errors"]:
            st.write("آخر الأخطاء:", st.session_state["_meta_api_errors"][-3:])
    st.warning(
        "⚠️ لا توجد بيانات متاحة حالياً من Meta عبر Windsor. "
        "تأكد من أن حساب Meta متصل بشكل صحيح على Windsor.ai، وأن الفترة المختارة فيها بيانات."
    )
    st.stop()

# ─────────────────────────────────────────────
# Normalize columns — MUST happen before the Debug table is shown,
# so any nested objects render as clean numbers, not "[object Object]".
# ─────────────────────────────────────────────
NUM_COLS = ["spend", "clicks", "impressions", "reach", "frequency",
            "actions_purchase", "action_values_purchase"]
for c in NUM_COLS:
    if c in df_meta.columns:
        df_meta[c] = df_meta[c].apply(safe_num)

df_meta["_purchases"] = df_meta["actions_purchase"] if "actions_purchase" in df_meta.columns else 0
df_meta["_purchase_value"] = df_meta["action_values_purchase"] if "action_values_purchase" in df_meta.columns else 0

# ─────────────────────────────────────────────
# Debug panel — shown AFTER normalization, so values are clean numbers
# ─────────────────────────────────────────────
with st.expander("🔍 Debug — البيانات الراجعة من Windsor (تأكد من الـ field names)"):
    st.write(f"عدد الصفوف: {len(df_meta)}")
    st.write(f"الأعمدة الراجعة: {list(df_meta.columns)}")
    st.dataframe(df_meta.head(15))

if level not in df_meta.columns:
    st.error(f"العمود '{level}' غير موجود في البيانات الراجعة. الأعمدة المتاحة: {list(df_meta.columns)}")
    st.stop()

# ─────────────────────────────────────────────
# Totals
# ─────────────────────────────────────────────
tot_spend = df_meta["spend"].sum() if "spend" in df_meta.columns else 0
tot_clicks = df_meta["clicks"].sum() if "clicks" in df_meta.columns else 0
tot_impressions = df_meta["impressions"].sum() if "impressions" in df_meta.columns else 0
tot_purchases = df_meta["_purchases"].sum()
tot_purchase_value = df_meta["_purchase_value"].sum()

ctr = (tot_clicks / tot_impressions * 100) if tot_impressions > 0 else 0
cpc = (tot_spend / tot_clicks) if tot_clicks > 0 else 0
cpa = (tot_spend / tot_purchases) if tot_purchases > 0 else 0
roas = (tot_purchase_value / tot_spend) if tot_spend > 0 else 0
aov = (tot_purchase_value / tot_purchases) if tot_purchases > 0 else 0

# ─────────────────────────────────────────────
# KPI Row
# ─────────────────────────────────────────────
st.markdown(section_header("Overview", "Meta Ads — Source of Truth"), unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(kpi_card("💰 Total Spend", fmt_currency(tot_spend), "Ad spend (Meta)", accent="#1877F2"), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("🛒 Purchases", fmt_number(tot_purchases), "Meta-attributed conversions", accent="#1D9E75"), unsafe_allow_html=True)
with c3: st.markdown(kpi_card("💵 Purchase Value", fmt_currency(tot_purchase_value), "Revenue per Meta", accent="#1D9E75"), unsafe_allow_html=True)
with c4: st.markdown(kpi_card("📈 ROAS", f"{roas:.2f}x" if roas else "—", "Purchase Value / Spend", accent="#7F77DD"), unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
c5, c6, c7, c8 = st.columns(4)
with c5: st.markdown(kpi_card("👁 Impressions", fmt_number(tot_impressions), "Total reach of ads", accent="#3266AD"), unsafe_allow_html=True)
with c6: st.markdown(kpi_card("🖱 Clicks", fmt_number(tot_clicks), f"CTR: {ctr:.2f}%", accent="#3266AD"), unsafe_allow_html=True)
with c7: st.markdown(kpi_card("💸 CPC", fmt_currency(cpc, 2), "Cost per click", accent="#EF9F27"), unsafe_allow_html=True)
with c8: st.markdown(kpi_card("🎯 CPA", fmt_currency(cpa, 0) if tot_purchases else "—", "Cost per purchase", accent="#EF9F27"), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Charts: Spend trend + ROAS trend
# ─────────────────────────────────────────────
if "date" in df_meta.columns:
    df_ts = df_meta.copy()
    df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
    df_ts = df_ts.dropna(subset=["date"]).groupby("date", as_index=False).sum(numeric_only=True).sort_values("date")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section_header("Spend vs Purchases Over Time", "", "#1877F2"), unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_ts["date"], y=df_ts["spend"], name="Spend", marker_color="#1877F2", opacity=0.7))
        fig.add_trace(go.Scatter(x=df_ts["date"], y=df_ts["_purchases"], name="Purchases", mode="lines+markers",
                                 line=dict(color="#1D9E75", width=2), yaxis="y2"))
        fig.update_layout(**PLOT_LAYOUT, height=280,
                          yaxis2=dict(overlaying="y", side="right", showgrid=False, color="#1D9E75"))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown(section_header("Purchase Value Over Time", "", "#1D9E75"), unsafe_allow_html=True)
        fig2 = px.area(df_ts, x="date", y="_purchase_value", color_discrete_sequence=["#1D9E75"])
        fig2.update_traces(fill="tozeroy", fillcolor="rgba(29,158,117,0.15)")
        fig2.update_layout(**PLOT_LAYOUT, height=280)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Campaign Performance Table
# ─────────────────────────────────────────────
st.markdown(section_header(f"{level_label} Performance", "Full breakdown", "#1877F2"), unsafe_allow_html=True)

agg_cols = {c: "sum" for c in ["spend", "clicks", "impressions", "_purchases", "_purchase_value"] if c in df_meta.columns}
df_lvl = df_meta.groupby(level, as_index=False).agg(agg_cols)
df_lvl = df_lvl[df_lvl["spend"] > 0].copy() if "spend" in df_lvl.columns else df_lvl
df_lvl["roas"] = df_lvl.apply(lambda r: r["_purchase_value"] / r["spend"] if r.get("spend", 0) > 0 else 0, axis=1)
df_lvl["cpa"] = df_lvl.apply(lambda r: r["spend"] / r["_purchases"] if r.get("_purchases", 0) > 0 else 0, axis=1)
df_lvl = df_lvl.sort_values("spend", ascending=False)

if not df_lvl.empty:
    rows = []
    for _, r in df_lvl.head(30).iterrows():
        rr = r["roas"]
        badge = '<span class="badge badge-green">قوي</span>' if rr >= 3 else ('<span class="badge badge-amber">متوسط</span>' if rr >= 1 else '<span class="badge badge-red">ضعيف</span>')
        rows.append(
            f"<tr><td style='font-size:12px'>{r[level]}</td>"
            f"<td>{fmt_currency(r.get('spend', 0))}</td>"
            f"<td>{fmt_number(r.get('clicks', 0))}</td>"
            f"<td>{int(r.get('_purchases', 0))}</td>"
            f"<td>{fmt_currency(r.get('_purchase_value', 0))}</td>"
            f"<td>{rr:.2f}x</td>"
            f"<td>{fmt_currency(r['cpa'], 0) if r.get('_purchases', 0) > 0 else '—'}</td>"
            f"<td>{badge}</td></tr>"
        )
    st.markdown(
        f"<table class='styled-table'><thead><tr><th>{level_label}</th><th>Spend</th><th>Clicks</th>"
        f"<th>Purchases</th><th>Revenue</th><th>ROAS</th><th>CPA</th><th>Rating</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>",
        unsafe_allow_html=True,
    )

    # Export
    import io
    buf = io.BytesIO()
    df_lvl.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("📥 Export CSV", buf.getvalue(), f"meta_{level}_performance.csv", "text/csv")
else:
    st.info("لا توجد بيانات صرف كافية لعرضها في هذا المستوى/الفترة.")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Top/Bottom performers
# ─────────────────────────────────────────────
if not df_lvl.empty and len(df_lvl) >= 2:
    col_top, col_bottom = st.columns(2)
    with col_top:
        st.markdown(section_header("🏆 Best ROAS", "", "#1D9E75"), unsafe_allow_html=True)
        best = df_lvl.sort_values("roas", ascending=False).head(5)
        fig_best = px.bar(best, x="roas", y=level, orientation="h", color_discrete_sequence=["#1D9E75"])
        fig_best.update_layout(**PLOT_LAYOUT, height=220, showlegend=False)
        st.plotly_chart(fig_best, use_container_width=True)
    with col_bottom:
        st.markdown(section_header("⚠️ Needs Review", "Lowest ROAS with spend", "#D85A30"), unsafe_allow_html=True)
        worst = df_lvl[df_lvl["spend"] > df_lvl["spend"].median()].sort_values("roas").head(5)
        fig_worst = px.bar(worst, x="roas", y=level, orientation="h", color_discrete_sequence=["#D85A30"])
        fig_worst.update_layout(**PLOT_LAYOUT, height=220, showlegend=False)
        st.plotly_chart(fig_worst, use_container_width=True)

st.markdown(
    '<div style="text-align:center;color:#334155;font-size:11px;margin-top:40px;padding:20px 0;'
    'border-top:1px solid rgba(255,255,255,0.06);">Raneen Meta Ads Dashboard · Streamlit + Plotly · Source: Meta via Windsor.ai</div>',
    unsafe_allow_html=True,
)
