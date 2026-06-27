import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, timedelta

from windsor import get_windsor_data, safe_num, fmt_currency, fmt_number, fmt_pct

# ── PAGE CONFIG ───────────────────────────────────────────
st.set_page_config(page_title="Raneen Analytics", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans Arabic', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.2rem 2rem 2rem; max-width: 1400px; }
section[data-testid="stSidebar"] { background: #F5F7FA; border-right: 1px solid #E2E6EA; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label { color: #73726C !important; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: .05em; }
.kpi-card { background: #FFFFFF; border: 1px solid #E2E6EA; border-radius: 12px; padding: 18px 20px; position: relative; overflow: hidden; transition: border-color .2s; }
.kpi-card:hover { border-color: #3266AD; }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 12px 12px 0 0; }
.kpi-label { font-size: 11px; color: #73726C; font-weight: 500; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.kpi-value { font-size: 26px; font-weight: 600; color: #1A1A2E; line-height: 1; margin-bottom: 6px; }
.kpi-change { font-size: 12px; } .kpi-sub { font-size: 11px; color: #9A9A8E; margin-top: 2px; }
.up { color: #1D9E75; } .down { color: #D85A30; } .warn { color: #EF9F27; } .neu { color: #888780; }
.section-header { display: flex; align-items: center; gap: 10px; padding: 6px 0 10px; border-bottom: 1px solid #E2E6EA; margin-bottom: 16px; }
.section-dot { width: 8px; height: 8px; border-radius: 50%; }
.section-title { font-size: 15px; font-weight: 600; color: #1A1A2E; }
.section-sub { font-size: 11px; color: #73726C; margin-left: auto; }
.insight-card { border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; font-size: 13px; line-height: 1.6; border-left: 4px solid; }
.insight-red { background: #FEF3EF; border-color: #D85A30; color: #A33A15; }
.insight-amber { background: #FEF9EF; border-color: #EF9F27; color: #8A5A10; }
.insight-green { background: #EAF7F2; border-color: #1D9E75; color: #0D6B4F; }
.insight-blue { background: #EAF0FB; border-color: #3266AD; color: #1A4A8A; }
.top-bar { display: flex; align-items: center; justify-content: space-between; padding: 10px 0 16px; border-bottom: 1px solid #E2E6EA; margin-bottom: 20px; }
.brand-name { font-size: 22px; font-weight: 700; color: #1A1A2E; } .brand-name span { color: #3266AD; }
.live-badge { display: inline-flex; align-items: center; gap: 6px; background: #EAF7F2; border: 1px solid rgba(29,158,117,.4); border-radius: 20px; padding: 4px 12px; font-size: 11px; font-weight: 500; color: #1D9E75; }
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: #1D9E75; animation: blink 2s ease-in-out infinite; display: inline-block; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.funnel-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.funnel-label { font-size: 12px; color: #73726C; min-width: 120px; }
.funnel-track { flex: 1; height: 28px; background: #F0F2F5; border-radius: 4px; overflow: hidden; }
.funnel-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 10px; font-size: 11px; font-weight: 600; color: #fff; }
.funnel-pct { font-size: 12px; min-width: 45px; text-align: right; font-weight: 600; }
.bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.bar-name { font-size: 12px; color: #73726C; min-width: 130px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; height: 8px; background: #F0F2F5; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }
.bar-val { font-size: 12px; color: #1A1A2E; min-width: 70px; text-align: right; font-weight: 500; }
.styled-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.styled-table th { background: #F5F7FA; color: #73726C; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; padding: 8px 10px; border-bottom: 1px solid #E2E6EA; text-align: left; }
.styled-table td { padding: 9px 10px; border-bottom: 1px solid #F0F2F5; color: #1A1A2E; vertical-align: middle; }
.styled-table tr:hover td { background: rgba(50,102,173,.06); }
.badge { display: inline-block; font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.badge-green { background: rgba(29,158,117,.2); color: #1D9E75; }
.badge-red { background: rgba(216,90,48,.2); color: #D85A30; }
.badge-amber { background: rgba(239,159,39,.2); color: #EF9F27; }
.badge-blue { background: rgba(50,102,173,.2); color: #3266AD; }
.badge-purple { background: rgba(127,119,221,.2); color: #7F77DD; }
.badge-gray { background: rgba(136,135,128,.2); color: #888780; }
.source-badge-web { background: rgba(50,102,173,.15); color: #3266AD; }
.source-badge-app { background: rgba(127,119,221,.15); color: #7F77DD; }
</style>
""", unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans Arabic", color="#73726C", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD", tickfont=dict(size=10)),
)

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="padding:16px 0 20px">
      <div style="font-size:18px;font-weight:700;color:#1A1A2E"><span style="color:#3266AD">●</span> Raneen</div>
      <div style="font-size:11px;color:#73726C;margin-top:4px">Analytics Dashboard — Web + App</div>
    </div>""", unsafe_allow_html=True)
    st.success("✅ Connected to GA4 (Web + App)", icon="📊")
    st.markdown("---")

    source_filter = st.radio(
        "Data Source",
        ["both", "web", "app"],
        format_func=lambda x: {"both": "🌐📱 Web + App", "web": "🌐 Web Only", "app": "📱 App Only"}.get(x, x),
        horizontal=False,
    )

    st.markdown("---")
    date_preset = st.selectbox("Date Range",
        ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month", "custom"],
        format_func=lambda x: {"last_7d": "Last 7 Days", "last_14d": "Last 14 Days", "last_30d": "Last 30 Days",
                                "last_90d": "Last 90 Days", "this_month": "This Month", "last_month": "Last Month",
                                "custom": "Custom Range"}.get(x, x))

    if date_preset == "custom":
        custom_from = st.date_input("From", date.today() - timedelta(days=30))
        custom_to = st.date_input("To", date.today() - timedelta(days=1))

    st.markdown("---")
    active_tab = st.radio("Section",
        ["Overview", "Funnel", "Traffic", "Devices", "E-Commerce", "Campaigns"],
        label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div style="font-size:10px;color:#9A9A8E;line-height:1.6">Data source: Google Analytics 4<br>via Windsor.ai<br><span style="color:#1D9E75">● Live</span> — refreshes on load</div>', unsafe_allow_html=True)

# ── TOP BAR ───────────────────────────────────────────────
source_label = {"both": "Web + App", "web": "Web Only", "app": "App Only"}.get(source_filter, "")
st.markdown(f"""<div class="top-bar">
  <div class="brand-name"><span>Raneen</span> Analytics — {source_label}</div>
  <div class="live-badge"><span class="live-dot"></span> Live via Windsor · GA4</div>
</div>""", unsafe_allow_html=True)

# ── Resolve custom dates ─────────────────────────
if date_preset == "custom":
    _d_from = str(custom_from)
    _d_to = str(custom_to)
else:
    _d_from, _d_to = None, None


# ── LOAD DATA (all aggregations now pull source=source_filter) ──
@st.cache_data(ttl=300, show_spinner=False)
def load_overview(preset, d_from, d_to, src):
    df1 = get_windsor_data(["date", "sessions", "active_users", "bounce_rate", "average_session_duration"], preset, d_from, d_to, source=src)
    df2 = get_windsor_data(["date", "purchase_revenue", "transactions", "add_to_carts", "checkouts"], preset, d_from, d_to, source=src)
    if df1.empty and df2.empty:
        return pd.DataFrame()
    if df1.empty:
        return df2
    if df2.empty:
        return df1
    try:
        return pd.merge(df1, df2, on=["date", "source"], how="outer")
    except Exception:
        return df1


@st.cache_data(ttl=300, show_spinner=False)
def load_channels(preset, d_from, d_to, src):
    df1 = get_windsor_data(["session_default_channel_group", "sessions"], preset, d_from, d_to, source=src)
    df2 = get_windsor_data(["session_default_channel_group", "purchase_revenue", "transactions", "add_to_carts", "checkouts"], preset, d_from, d_to, source=src)
    if df1.empty and df2.empty:
        return pd.DataFrame()
    if df1.empty:
        return df2
    if df2.empty:
        return df1
    try:
        return pd.merge(df1, df2, on=["session_default_channel_group", "source"], how="outer")
    except Exception:
        return df1


@st.cache_data(ttl=300, show_spinner=False)
def load_devices(preset, d_from, d_to, src):
    df1 = get_windsor_data(["devicecategory", "sessions", "bounce_rate", "engagement_rate"], preset, d_from, d_to, source=src)
    df2 = get_windsor_data(["devicecategory", "purchase_revenue", "transactions"], preset, d_from, d_to, source=src)
    if df1.empty and df2.empty:
        return pd.DataFrame()
    if df1.empty:
        return df2
    if df2.empty:
        return df1
    try:
        return pd.merge(df1, df2, on=["devicecategory", "source"], how="outer")
    except Exception:
        return df1


@st.cache_data(ttl=300, show_spinner=False)
def load_new_returning(preset, d_from, d_to, src):
    df1 = get_windsor_data(["new_vs_returning", "sessions", "active_users"], preset, d_from, d_to, source=src)
    df2 = get_windsor_data(["new_vs_returning", "purchase_revenue", "transactions"], preset, d_from, d_to, source=src)
    if df1.empty and df2.empty:
        return pd.DataFrame()
    if df1.empty:
        return df2
    if df2.empty:
        return df1
    try:
        return pd.merge(df1, df2, on=["new_vs_returning", "source"], how="outer")
    except Exception:
        return df1


@st.cache_data(ttl=300, show_spinner=False)
def load_campaigns(preset, d_from, d_to, src):
    df1 = get_windsor_data(["session_google_ads_campaign_name", "sessions"], preset, d_from, d_to, source=src)
    df2 = get_windsor_data(["session_google_ads_campaign_name", "purchase_revenue", "transactions", "add_to_carts", "checkouts"], preset, d_from, d_to, source=src)
    if df1.empty and df2.empty:
        return pd.DataFrame()
    if df1.empty:
        return df2
    if df2.empty:
        return df1
    try:
        return pd.merge(df1, df2, on=["session_google_ads_campaign_name", "source"], how="outer")
    except Exception:
        return df1


@st.cache_data(ttl=300, show_spinner=False)
def load_categories(preset, d_from, d_to, src):
    return get_windsor_data(["item_category", "gross_item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"], preset, d_from, d_to, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def load_products(preset, d_from, d_to, src):
    return get_windsor_data(["item_name", "item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"], preset, d_from, d_to, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def load_subcategory(preset, d_from, d_to, src):
    return get_windsor_data(["item_category", "item_category2", "gross_item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"], preset, d_from, d_to, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def load_campaign_products(preset, d_from, d_to, src):
    return get_windsor_data(["session_google_ads_campaign_name", "item_name", "item_revenue", "items_purchased"], preset, d_from, d_to, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def load_meta_campaigns(preset, d_from, d_to, src):
    return get_windsor_data(["session_manual_campaign_name", "sessions", "purchase_revenue", "transactions", "add_to_carts"], preset, d_from, d_to, source=src)


with st.spinner("⏳ Loading GA4 data (Web + App)..."):
    df_ov = load_overview(date_preset, _d_from, _d_to, source_filter)
    df_ch = load_channels(date_preset, _d_from, _d_to, source_filter)
    df_dv = load_devices(date_preset, _d_from, _d_to, source_filter)
    df_nr = load_new_returning(date_preset, _d_from, _d_to, source_filter)
    df_cp = load_campaigns(date_preset, _d_from, _d_to, source_filter)

if df_ov.empty:
    st.error("❌ Could not load data. Windsor API error — check logs, or try refreshing.")
    st.stop()

# ── TOTALS ────────────────────────────────────────────────
tot_sessions = safe_num(df_ov["sessions"].sum()) if "sessions" in df_ov else 0
tot_revenue = safe_num(df_ov["purchase_revenue"].sum()) if "purchase_revenue" in df_ov else 0
tot_orders = safe_num(df_ov["transactions"].sum()) if "transactions" in df_ov else 0
tot_carts = safe_num(df_ov["add_to_carts"].sum()) if "add_to_carts" in df_ov else 0
tot_checkouts = safe_num(df_ov["checkouts"].sum()) if "checkouts" in df_ov else 0
avg_bounce = safe_num(df_ov["bounce_rate"].mean()) * 100 if "bounce_rate" in df_ov else 0
avg_session = safe_num(df_ov["average_session_duration"].mean()) if "average_session_duration" in df_ov else 0
aov = tot_revenue / tot_orders if tot_orders > 0 else 0
cvr = tot_orders / tot_sessions * 100 if tot_sessions > 0 else 0
cart_abandon = (1 - tot_orders / tot_carts) * 100 if tot_carts > 0 else 0
avg_session_m = int(avg_session // 60)
avg_session_s = int(avg_session % 60)


# ── UI HELPERS ────────────────────────────────────────────
def kpi_card(label, value, change_txt, change_cls, sub="", accent_color="#3266AD"):
    return f"""<div class="kpi-card"><div class="kpi-accent" style="background:{accent_color}"></div>
    <div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>
    <div class="kpi-change {change_cls}">{change_txt}</div>
    {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}</div>"""


def section_header(title, sub="", color="#3266AD"):
    return f"""<div class="section-header"><div class="section-dot" style="background:{color}"></div>
    <div class="section-title">{title}</div>
    {'<div class="section-sub">' + sub + '</div>' if sub else ''}</div>"""


def bar_html(name, pct, color, val_str):
    return f"""<div class="bar-row"><div class="bar-name">{name}</div>
    <div class="bar-track"><div class="bar-fill" style="width:{max(pct,1)}%;background:{color}"></div></div>
    <div class="bar-val">{val_str}</div></div>"""


def insight(icon, title, body, cls):
    return f'<div class="insight-card {cls}"><b>{icon} {title}</b><br/>{body}</div>'


def export_csv_button(df, filename="export.csv", label="📥 Export CSV"):
    import io
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button(label=label, data=buf.getvalue(), file_name=filename, mime="text/csv", use_container_width=False)


def source_badge(src):
    if src == "web":
        return '<span class="badge source-badge-web">🌐 Web</span>'
    elif src == "app":
        return '<span class="badge source-badge-app">📱 App</span>'
    return ""


# ═══════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════
if active_tab == "Overview":
    st.markdown(section_header("Overview", "Key Performance Indicators", "#3266AD"), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi_card("Sessions", fmt_number(tot_sessions), "▲ Live GA4 Data", "up", accent_color="#3266AD"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Revenue", fmt_currency(tot_revenue), "▲ Purchase Revenue", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Orders", fmt_number(tot_orders), "▲ Transactions", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("AOV", fmt_currency(aov, 0), "متوسط قيمة الطلب", "neu", accent_color="#3266AD"), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5: st.markdown(kpi_card("Add to Cart", fmt_number(tot_carts), f"⚠ Cart Abandon {cart_abandon:.1f}%", "warn", accent_color="#EF9F27"), unsafe_allow_html=True)
    with c6: st.markdown(kpi_card("Bounce Rate", fmt_pct(avg_bounce), "▼ Monitor carefully", "down" if avg_bounce > 50 else "warn", accent_color="#D85A30"), unsafe_allow_html=True)
    with c7: st.markdown(kpi_card("Avg Session", f"{avg_session_m}:{avg_session_s:02d} min", "▲ Engagement", "up", accent_color="#7F77DD"), unsafe_allow_html=True)
    with c8: st.markdown(kpi_card("CVR", fmt_pct(cvr, 2), "⚠ Needs improvement" if cvr < 1 else "▲ Good", "warn" if cvr < 1 else "up", accent_color="#D85A30" if cvr < 1 else "#1D9E75"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Web vs App split (only shown when source_filter == "both") ──
    if source_filter == "both" and "source" in df_ov.columns:
        st.markdown(section_header("Web vs App Split", "Revenue & Sessions by Source", "#7F77DD"), unsafe_allow_html=True)
        split = df_ov.groupby("source").agg(
            sessions=("sessions", "sum"),
            purchase_revenue=("purchase_revenue", "sum"),
            transactions=("transactions", "sum"),
        ).reset_index()

        col_w, col_a = st.columns(2)
        web_row = split[split["source"] == "web"]
        app_row = split[split["source"] == "app"]

        with col_w:
            rev_w = safe_num(web_row["purchase_revenue"].sum()) if not web_row.empty else 0
            ses_w = safe_num(web_row["sessions"].sum()) if not web_row.empty else 0
            ord_w = safe_num(web_row["transactions"].sum()) if not web_row.empty else 0
            st.markdown(kpi_card("🌐 Web Revenue", fmt_currency(rev_w), f"{fmt_number(ses_w)} sessions · {fmt_number(ord_w)} orders", "up", accent_color="#3266AD"), unsafe_allow_html=True)

        with col_a:
            rev_a = safe_num(app_row["purchase_revenue"].sum()) if not app_row.empty else 0
            ses_a = safe_num(app_row["sessions"].sum()) if not app_row.empty else 0
            ord_a = safe_num(app_row["transactions"].sum()) if not app_row.empty else 0
            st.markdown(kpi_card("📱 App Revenue", fmt_currency(rev_a), f"{fmt_number(ses_a)} sessions · {fmt_number(ord_a)} orders", "up", accent_color="#7F77DD"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        fig_split = go.Figure(go.Pie(
            labels=["Web", "App"], values=[rev_w, rev_a],
            marker_colors=["#3266AD", "#7F77DD"], hole=0.6,
            textinfo="label+percent", textfont_size=12,
        ))
        fig_split.update_layout(**PLOT_LAYOUT, height=240)
        st.plotly_chart(fig_split, use_container_width=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if "date" in df_ov.columns:
        df_ts = df_ov.copy()
        df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
        df_ts = df_ts.dropna(subset=["date"])
        # Aggregate across source if "both" is selected, so the time series is combined
        df_ts = df_ts.groupby("date", as_index=False).sum(numeric_only=True).sort_values("date")

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue Over Time", "", "#1D9E75"), unsafe_allow_html=True)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=df_ts["date"], y=df_ts["purchase_revenue"] / 1000, name="Revenue K ج", marker_color="#3266AD", opacity=0.8), secondary_y=False)
            fig.add_trace(go.Scatter(x=df_ts["date"], y=df_ts["transactions"], name="Orders", line=dict(color="#1D9E75", width=2), mode="lines+markers", marker_size=4), secondary_y=True)
            fig.update_layout(**PLOT_LAYOUT, height=260)
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown(section_header("Sessions & Bounce Rate", "", "#D85A30"), unsafe_allow_html=True)
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig2.add_trace(go.Bar(x=df_ts["date"], y=df_ts["sessions"] / 1000, name="Sessions K", marker_color="rgba(50,102,173,0.7)"), secondary_y=False)
            if "bounce_rate" in df_ts.columns:
                fig2.add_trace(go.Scatter(x=df_ts["date"], y=df_ts["bounce_rate"] * 100, name="Bounce %", line=dict(color="#D85A30", width=2), mode="lines", fill="tozeroy", fillcolor="rgba(216,90,48,0.1)"), secondary_y=True)
            fig2.update_layout(**PLOT_LAYOUT, height=260)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown(section_header("New vs Returning", "Revenue Split", "#7F77DD"), unsafe_allow_html=True)
    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        nr = df_nr[df_nr["new_vs_returning"].isin(["new", "returning"])].copy()
        for col in ["purchase_revenue", "sessions", "transactions"]:
            if col in nr.columns:
                nr[col] = nr[col].apply(safe_num)
        ret = nr[nr["new_vs_returning"] == "returning"]
        new = nr[nr["new_vs_returning"] == "new"]
        ret_rev = ret["purchase_revenue"].sum()
        new_rev = new["purchase_revenue"].sum()
        tot_r = ret_rev + new_rev
        ret_pct = ret_rev / tot_r * 100 if tot_r else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(kpi_card("Returning Sessions", fmt_number(ret["sessions"].sum()), "Loyal customers", "neu", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("Returning Revenue", fmt_currency(ret_rev), f"▲ {ret_pct:.1f}% of total", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c3:
            rc = ret["transactions"].sum() / ret["sessions"].sum() * 100 if ret["sessions"].sum() > 0 else 0
            st.markdown(kpi_card("Returning CVR", fmt_pct(rc, 2), "vs New users", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c4:
            nc = new["transactions"].sum() / new["sessions"].sum() * 100 if new["sessions"].sum() > 0 else 0
            st.markdown(kpi_card("New Users CVR", fmt_pct(nc, 2), "Lower than returning", "warn", accent_color="#3266AD"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# FUNNEL
# ═══════════════════════════════════════════════════════════
elif active_tab == "Funnel":
    st.markdown(section_header("Sales Funnel", "Item Views → Purchase", "#3266AD"), unsafe_allow_html=True)

    with st.spinner("Loading funnel data..."):
        df_funnel_items = load_categories(date_preset, _d_from, _d_to, source_filter)

    tot_items_viewed = safe_num(df_funnel_items["items_viewed"].sum()) if not df_funnel_items.empty and "items_viewed" in df_funnel_items.columns else 0
    tot_items_carted = safe_num(df_funnel_items["items_added_to_cart"].sum()) if not df_funnel_items.empty and "items_added_to_cart" in df_funnel_items.columns else 0

    base_val = tot_items_viewed if tot_items_viewed > 0 else tot_sessions
    base_label = "Items Viewed" if tot_items_viewed > 0 else "Sessions"

    funnel_steps = [
        (base_label, base_val, 100.0, "#3266AD"),
        ("Add to Cart", tot_items_carted if tot_items_carted > 0 else tot_carts,
         (tot_items_carted / base_val * 100 if base_val else 0) if tot_items_carted > 0 else (tot_carts / base_val * 100 if base_val else 0), "#378ADD"),
        ("Checkout Start", tot_checkouts, tot_checkouts / base_val * 100 if base_val else 0, "#85B7EB"),
        ("Purchase", tot_orders, tot_orders / base_val * 100 if base_val else 0, "#1D9E75"),
    ]

    for label, count, pct, color in funnel_steps:
        bw = max(pct, 0.5)
        st.markdown(f"""<div class="funnel-row"><div class="funnel-label">{label}</div>
        <div class="funnel-track"><div class="funnel-fill" style="width:{bw}%;background:{color}">
        {'&nbsp;' + fmt_number(count) if bw > 8 else ''}</div></div>
        <div class="funnel-pct" style="color:{color}">{pct:.2f}%</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    _cart_v = tot_items_carted if tot_items_carted > 0 else tot_carts
    view_drop = (1 - _cart_v / base_val) * 100 if base_val else 0
    chk_drop = (1 - tot_checkouts / _cart_v) * 100 if _cart_v else 0
    pur_drop = (1 - tot_orders / tot_checkouts) * 100 if tot_checkouts else 0

    with c1: st.markdown(kpi_card("View → Cart", fmt_pct(100 - view_drop, 1), f"⚠ {view_drop:.1f}% drop", "warn", accent_color="#EF9F27"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Cart → Checkout", fmt_pct(100 - chk_drop, 1), f"⚠ {chk_drop:.1f}% abandon", "down", accent_color="#D85A30"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Checkout → Buy", fmt_pct(100 - pur_drop, 1), f"⚠ {pur_drop:.1f}% drop", "down" if pur_drop > 50 else "warn", accent_color="#D85A30"), unsafe_allow_html=True)

    fig = go.Figure(go.Funnel(
        y=[base_label, "Add to Cart", "Checkout", "Purchase"],
        x=[base_val, _cart_v, tot_checkouts, tot_orders],
        textinfo="value+percent initial",
        marker=dict(color=["#3266AD", "#378ADD", "#85B7EB", "#1D9E75"])))
    fig.update_layout(**PLOT_LAYOUT, height=320)
    st.plotly_chart(fig, use_container_width=True)

    # ── Funnel by Source (Web vs App), shown when "both" selected ──
    if source_filter == "both" and "source" in df_funnel_items.columns:
        st.markdown(section_header("Funnel by Source", "Web vs App Comparison", "#7F77DD"), unsafe_allow_html=True)
        for col in ["items_viewed", "items_added_to_cart", "items_purchased"]:
            if col in df_funnel_items.columns:
                df_funnel_items[col] = df_funnel_items[col].apply(safe_num)
        by_src = df_funnel_items.groupby("source").sum(numeric_only=True).reset_index()
        rows = []
        for _, r in by_src.iterrows():
            v = safe_num(r.get("items_viewed", 0))
            c = safe_num(r.get("items_added_to_cart", 0))
            p = safe_num(r.get("items_purchased", 0))
            v2c = c / v * 100 if v > 0 else 0
            c2p = p / c * 100 if c > 0 else 0
            badge = source_badge(r["source"])
            rows.append(f"<tr><td>{badge}</td><td>{fmt_number(v)}</td><td>{fmt_number(c)}</td><td>{v2c:.2f}%</td><td>{fmt_number(p)}</td><td>{c2p:.2f}%</td></tr>")
        st.markdown(f"<table class='styled-table'><thead><tr><th>Source</th><th>Views</th><th>Carts</th><th>View→Cart</th><th>Purchases</th><th>Cart→Buy</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)

    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        st.markdown(section_header("New vs Returning — Funnel Comparison", "", "#7F77DD"), unsafe_allow_html=True)
        nr = df_nr[df_nr["new_vs_returning"].isin(["new", "returning"])].copy()
        for col in ["sessions", "purchase_revenue", "transactions"]:
            if col in nr.columns:
                nr[col] = nr[col].apply(safe_num)
        rows = []
        for seg in ["returning", "new"]:
            d = nr[nr["new_vs_returning"] == seg]
            ses = d["sessions"].sum()
            rev = d["purchase_revenue"].sum()
            txn = d["transactions"].sum()
            _cvr = txn / ses * 100 if ses > 0 else 0
            _aov = rev / txn if txn > 0 else 0
            bc = "badge-green" if seg == "returning" else "badge-blue"
            bl = seg.title()
            rows.append(f"<tr><td><span class='badge {bc}'>{bl}</span></td><td>{fmt_number(ses)}</td><td>{fmt_currency(rev)}</td><td>{fmt_number(txn)}</td><td><b style='color:{'#1D9E75' if seg=='returning' else '#EF9F27'}'>{fmt_pct(_cvr,2)}</b></td><td>{fmt_currency(_aov,0)}</td></tr>")
        st.markdown(f"<table class='styled-table'><thead><tr><th>Segment</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# TRAFFIC
# ═══════════════════════════════════════════════════════════
elif active_tab == "Traffic":
    st.markdown(section_header("Traffic Sources", "Sessions & Revenue by Channel", "#3266AD"), unsafe_allow_html=True)

    if not df_ch.empty and "session_default_channel_group" in df_ch.columns:
        for col in ["sessions", "purchase_revenue", "transactions", "add_to_carts"]:
            if col in df_ch.columns:
                df_ch[col] = df_ch[col].apply(safe_num)
        df_g = df_ch[df_ch["session_default_channel_group"].notna() & (df_ch["session_default_channel_group"] != "")]
        df_g = df_g.groupby("session_default_channel_group").sum(numeric_only=True).reset_index()
        df_g = df_g[df_g["sessions"] > 10].sort_values("purchase_revenue", ascending=False)

        COLORS = ["#3266AD", "#378ADD", "#85B7EB", "#1D9E75", "#5DCAA5", "#EF9F27", "#888780", "#7F77DD"]
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Sessions by Channel**")
            mx = df_g["sessions"].max()
            for i, (_, r) in enumerate(df_g.head(8).iterrows()):
                st.markdown(bar_html(r["session_default_channel_group"], r["sessions"] / mx * 100 if mx else 0, COLORS[i % len(COLORS)], fmt_number(r["sessions"])), unsafe_allow_html=True)
        with col_r:
            st.markdown("**Revenue by Channel**")
            mx = df_g["purchase_revenue"].max()
            for i, (_, r) in enumerate(df_g.sort_values("purchase_revenue", ascending=False).head(8).iterrows()):
                st.markdown(bar_html(r["session_default_channel_group"], r["purchase_revenue"] / mx * 100 if mx else 0, COLORS[i % len(COLORS)], fmt_currency(r["purchase_revenue"])), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(section_header("Channel Efficiency", "CVR & Revenue per Session", "#EF9F27"), unsafe_allow_html=True)
        rows = []
        for _, r in df_g.iterrows():
            ses = r["sessions"]
            rev = r["purchase_revenue"]
            txn = r["transactions"]
            _cvr = txn / ses * 100 if ses > 0 else 0
            rps = rev / ses if ses > 0 else 0
            if _cvr >= 1.5:
                badge = '<span class="badge badge-green">الأقوى</span>'
            elif _cvr >= 0.8:
                badge = '<span class="badge badge-blue">جيد</span>'
            elif _cvr >= 0.4:
                badge = '<span class="badge badge-amber">راجع</span>'
            else:
                badge = '<span class="badge badge-red">ضعيف</span>'
            rows.append(f"<tr><td><b>{r['session_default_channel_group']}</b></td><td>{fmt_number(ses)}</td><td>{fmt_currency(rev)}</td><td>{fmt_number(txn)}</td><td><b style='color:{'#1D9E75' if _cvr>=1 else '#EF9F27' if _cvr>=0.5 else '#D85A30'}'>{fmt_pct(_cvr,2)}</b></td><td>{fmt_currency(rps,1)}</td><td>{badge}</td></tr>")
        st.markdown(f"<table class='styled-table'><thead><tr><th>Channel</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Session</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        export_csv_button(df_g[["session_default_channel_group", "sessions", "purchase_revenue", "transactions"]], "channels.csv")
    else:
        st.info("مفيش بيانات channels متاحة لهذا الفلتر.")


# ═══════════════════════════════════════════════════════════
# DEVICES
# ═══════════════════════════════════════════════════════════
elif active_tab == "Devices":
    st.markdown(section_header("Device Performance", "Mobile vs Desktop vs Tablet", "#7F77DD"), unsafe_allow_html=True)

    if not df_dv.empty and "devicecategory" in df_dv.columns:
        for col in ["sessions", "purchase_revenue", "transactions", "bounce_rate"]:
            if col in df_dv.columns:
                df_dv[col] = df_dv[col].apply(safe_num)
        DC = {"mobile": "#3266AD", "desktop": "#888780", "tablet": "#1D9E75"}
        md = df_dv[df_dv["devicecategory"].isin(["mobile", "desktop", "tablet"])]
        md = md.groupby("devicecategory").sum(numeric_only=True).reset_index()

        cols = st.columns(len(md)) if len(md) else [st.container()]
        for i, (_, r) in enumerate(md.iterrows()):
            dev = r["devicecategory"]
            c = DC.get(dev, "#888780")
            br = r["bounce_rate"] * 100
            sp = r["sessions"] / md["sessions"].sum() * 100 if md["sessions"].sum() > 0 else 0
            with cols[i]:
                st.markdown(kpi_card(dev.title(), f"{sp:.1f}%", f"Bounce: {br:.1f}%", "down" if br > 55 else "warn" if br > 45 else "up", f"Sessions: {fmt_number(r['sessions'])} · Rev: {fmt_currency(r['purchase_revenue'])}", accent_color=c), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue Split", "", "#1D9E75"), unsafe_allow_html=True)
            fig = go.Figure(go.Pie(labels=md["devicecategory"].str.title(), values=md["purchase_revenue"], marker_colors=[DC.get(d, "#888780") for d in md["devicecategory"]], hole=0.6, textinfo="label+percent", textfont_size=11))
            fig.update_layout(**PLOT_LAYOUT, height=260)
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            st.markdown(section_header("Bounce Rate by Device", "", "#D85A30"), unsafe_allow_html=True)
            fig2 = go.Figure(go.Bar(x=md["devicecategory"].str.title(), y=md["bounce_rate"] * 100, marker_color=[DC.get(d, "#888780") for d in md["devicecategory"]], text=[f"{r*100:.1f}%" for r in md["bounce_rate"]], textposition="outside"))
            fig2.update_layout(**PLOT_LAYOUT, height=260, yaxis=dict(ticksuffix="%", range=[0, 80], gridcolor="#E8EDF2"))
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("مفيش بيانات devices متاحة لهذا الفلتر.")


# ═══════════════════════════════════════════════════════════
# E-COMMERCE
# ═══════════════════════════════════════════════════════════
elif active_tab == "E-Commerce":
    st.markdown(section_header("E-Commerce Insights", "Products & Categories", "#1D9E75"), unsafe_allow_html=True)

    with st.spinner("Loading e-commerce data..."):
        df_cat = load_categories(date_preset, _d_from, _d_to, source_filter)
        df_prod = load_products(date_preset, _d_from, _d_to, source_filter)
        df_sub = load_subcategory(date_preset, _d_from, _d_to, source_filter)

    RANEEN_CATS = ["الأجهزة المنزلية", "الأثاث", "الإلكترونيات", "المطبخ", "موبايلات", "المفروشات", "عروض رنين", "المنزل", "المنتجات العائلية", "الأزياء و الموضة"]
    CAT_ICONS = {"الأجهزة المنزلية": "🏠", "الأثاث": "🛋️", "الإلكترونيات": "📺", "المطبخ": "🍳", "موبايلات": "📱", "المفروشات": "🛏️", "عروض رنين": "🏷️", "المنزل": "🪴", "المنتجات العائلية": "👨‍👩‍👧", "الأزياء و الموضة": "👗"}
    CAT_COLORS = ["#3266AD", "#378ADD", "#85B7EB", "#1D9E75", "#5DCAA5", "#EF9F27", "#7F77DD", "#D85A30", "#888780", "#B5D4F4"]

    if not df_cat.empty and "item_category" in df_cat.columns:
        for col in ["gross_item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"]:
            if col in df_cat.columns:
                df_cat[col] = df_cat[col].apply(safe_num)
        df_cat_agg = df_cat.groupby("item_category").sum(numeric_only=True).reset_index()
        df_cf = df_cat_agg[df_cat_agg["item_category"].isin(RANEEN_CATS)].sort_values("gross_item_revenue", ascending=False)
        tir = df_cf["gross_item_revenue"].sum()
        tiu = df_cf["items_purchased"].sum()

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(kpi_card("Item Revenue", fmt_currency(tir), "All categories", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("Units Sold", fmt_number(tiu), "Total items purchased", "up", accent_color="#3266AD"), unsafe_allow_html=True)
        with c3: st.markdown(kpi_card("Avg Unit Price", fmt_currency(tir / tiu, 0) if tiu else "—", "Revenue / Units", "neu", accent_color="#7F77DD"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue by Category", "", "#1D9E75"), unsafe_allow_html=True)
            mx = df_cf["gross_item_revenue"].max()
            for i, (_, r) in enumerate(df_cf.head(10).iterrows()):
                st.markdown(bar_html(f"{CAT_ICONS.get(r['item_category'],'')} {r['item_category']}", r["gross_item_revenue"] / mx * 100 if mx else 0, CAT_COLORS[i % len(CAT_COLORS)], fmt_currency(r["gross_item_revenue"])), unsafe_allow_html=True)
        with col_r:
            st.markdown(section_header("Cart-to-View Rate", "", "#EF9F27"), unsafe_allow_html=True)
            df_cf = df_cf.copy()
            df_cf["cr"] = df_cf.apply(lambda r: r["items_added_to_cart"] / r["items_viewed"] * 100 if r["items_viewed"] > 0 else 0, axis=1)
            mx = df_cf["cr"].max()
            for _, r in df_cf.sort_values("cr", ascending=False).head(10).iterrows():
                c = "#1D9E75" if r["cr"] > 6 else "#EF9F27" if r["cr"] > 3 else "#D85A30"
                st.markdown(bar_html(f"{CAT_ICONS.get(r['item_category'],'')} {r['item_category']}", r["cr"] / mx * 100 if mx else 0, c, f"{r['cr']:.1f}%"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(section_header("Category Drill-Down", "إيه بيباع جوه كل فئة؟", "#7F77DD"), unsafe_allow_html=True)
        sel_cat = st.selectbox("اختار الفئة", RANEEN_CATS, key="cat_dd")

        if not df_sub.empty and "item_category2" in df_sub.columns:
            for col in ["gross_item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"]:
                if col in df_sub.columns:
                    df_sub[col] = df_sub[col].apply(safe_num)
            dsf = df_sub[(df_sub["item_category"] == sel_cat) & df_sub["item_category2"].notna() & (df_sub["item_category2"] != "") & (df_sub["item_category2"] != "(not set)")]
            dsf = dsf.groupby("item_category2").sum(numeric_only=True).reset_index()
            dsf = dsf[dsf["gross_item_revenue"] > 0].sort_values("gross_item_revenue", ascending=False)

            if not dsf.empty:
                SC = ["#3266AD", "#1D9E75", "#EF9F27", "#7F77DD", "#D85A30", "#5DCAA5", "#85B7EB", "#888780"]
                col_l2, col_r2 = st.columns(2)
                mx = dsf["gross_item_revenue"].max()
                with col_l2:
                    st.markdown(f"**Revenue — {sel_cat}**")
                    for i, (_, r) in enumerate(dsf.head(10).iterrows()):
                        st.markdown(bar_html(str(r["item_category2"]), r["gross_item_revenue"] / mx * 100 if mx else 0, SC[i % len(SC)], fmt_currency(r["gross_item_revenue"])), unsafe_allow_html=True)
                with col_r2:
                    st.markdown(f"**Units — {sel_cat}**")
                    du = dsf.sort_values("items_purchased", ascending=False)
                    mu = du["items_purchased"].max()
                    for i, (_, r) in enumerate(du.head(10).iterrows()):
                        st.markdown(bar_html(str(r["item_category2"]), r["items_purchased"] / mu * 100 if mu else 0, SC[i % len(SC)], fmt_number(r["items_purchased"]) + " unit"), unsafe_allow_html=True)
            else:
                st.info(f"مفيش sub-category data لـ '{sel_cat}'")

        if not df_prod.empty and "item_name" in df_prod.columns:
            for col in ["item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"]:
                if col in df_prod.columns:
                    df_prod[col] = df_prod[col].apply(safe_num)
            df_prod_agg = df_prod.groupby("item_name").sum(numeric_only=True).reset_index()
            df_top = df_prod_agg[df_prod_agg["item_revenue"] > 0].sort_values("item_revenue", ascending=False).head(15)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown(section_header("Top 15 Products by Revenue", "", "#3266AD"), unsafe_allow_html=True)
            rows = []
            for i, (_, r) in enumerate(df_top.iterrows(), 1):
                nm = str(r["item_name"])[:55] + ("..." if len(str(r["item_name"])) > 55 else "")
                vw = safe_num(r.get("items_viewed", 0))
                cr_ = safe_num(r.get("items_added_to_cart", 0)) / vw * 100 if vw > 0 else 0
                bc = "badge-green" if cr_ > 8 else "badge-amber" if cr_ > 4 else "badge-red"
                rows.append(f"<tr><td style='color:#9A9A8E'>{i}</td><td>{nm}</td><td><b style='color:#1D9E75'>{fmt_currency(r['item_revenue'])}</b></td><td>{int(r['items_purchased'])}</td><td>{fmt_number(vw)}</td><td><span class='badge {bc}'>{cr_:.1f}%</span></td></tr>")
            st.markdown(f"<table class='styled-table'><thead><tr><th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>Views</th><th>Cart%</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
            export_csv_button(df_top[["item_name", "item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"]], "top_products.csv")
    else:
        st.info("مفيش بيانات e-commerce متاحة لهذا الفلتر.")


# ═══════════════════════════════════════════════════════════
# CAMPAIGNS
# ═══════════════════════════════════════════════════════════
elif active_tab == "Campaigns":
    st.markdown(section_header("Campaigns Performance", "Google Ads Analysis", "#3266AD"), unsafe_allow_html=True)

    if not df_cp.empty and "session_google_ads_campaign_name" in df_cp.columns:
        for col in ["sessions", "purchase_revenue", "transactions", "add_to_carts", "checkouts"]:
            if col in df_cp.columns:
                df_cp[col] = df_cp[col].apply(safe_num)
        df_cp_agg = df_cp.groupby("session_google_ads_campaign_name").sum(numeric_only=True).reset_index()
        df_p = df_cp_agg[df_cp_agg["session_google_ads_campaign_name"].notna() & (df_cp_agg["session_google_ads_campaign_name"] != "(not set)") & (df_cp_agg["sessions"] > 100)].copy()
        df_p["cvr"] = df_p.apply(lambda r: r["transactions"] / r["sessions"] * 100 if r["sessions"] > 0 else 0, axis=1)
        df_p["rps"] = df_p.apply(lambda r: r["purchase_revenue"] / r["sessions"] if r["sessions"] > 0 else 0, axis=1)
        df_p = df_p.sort_values("purchase_revenue", ascending=False)

        if not df_p.empty:
            best = df_p.loc[df_p["purchase_revenue"].idxmax()]
            worst = df_p.loc[df_p["cvr"].idxmin()]
            bcvr = df_p.loc[df_p["cvr"].idxmax()]

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(kpi_card("Best Campaign", best["session_google_ads_campaign_name"].split("-")[-1], fmt_currency(best["purchase_revenue"]), "up", accent_color="#3266AD"), unsafe_allow_html=True)
            with c2: st.markdown(kpi_card("Highest CVR", bcvr["session_google_ads_campaign_name"].split("-")[-1], fmt_pct(bcvr["cvr"], 2), "up", accent_color="#1D9E75"), unsafe_allow_html=True)
            with c3: st.markdown(kpi_card("Total Paid Sessions", fmt_number(df_p["sessions"].sum()), "Google Ads campaigns", "neu", accent_color="#7F77DD"), unsafe_allow_html=True)
            with c4: st.markdown(kpi_card("Worst CVR", worst["session_google_ads_campaign_name"].split("-")[-1], fmt_pct(worst["cvr"], 2), "down", accent_color="#D85A30"), unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown(section_header("Revenue per Session", "Campaign Efficiency", "#EF9F27"), unsafe_allow_html=True)
                dr = df_p.sort_values("rps", ascending=False).head(10)
                mx = dr["rps"].max()
                for _, r in dr.iterrows():
                    p = r["rps"] / mx * 100 if mx else 0
                    c = "#1D9E75" if p > 70 else "#EF9F27" if p > 30 else "#D85A30"
                    st.markdown(bar_html(str(r["session_google_ads_campaign_name"])[-28:], p, c, fmt_currency(r["rps"], 1)), unsafe_allow_html=True)
            with col_r:
                st.markdown(section_header("Sessions vs Revenue", "Bubble View", "#3266AD"), unsafe_allow_html=True)
                fig = px.scatter(df_p.head(12), x="sessions", y="purchase_revenue", size="transactions", color="cvr", hover_name="session_google_ads_campaign_name", color_continuous_scale=["#D85A30", "#EF9F27", "#1D9E75"], size_max=40)
                fig.update_layout(**PLOT_LAYOUT, height=280)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown(section_header("All Campaigns — Full Analysis", "", "#2A3050"), unsafe_allow_html=True)
            rows = []
            for _, r in df_p.iterrows():
                cv = r["cvr"]
                if cv >= 1.5:
                    badge = '<span class="badge badge-green">الأقوى</span>'
                elif cv >= 0.8:
                    badge = '<span class="badge badge-blue">جيد</span>'
                elif cv >= 0.3:
                    badge = '<span class="badge badge-amber">راجع</span>'
                else:
                    badge = '<span class="badge badge-red">ضعيف</span>'
                rows.append(f"<tr><td style='font-size:11px'>{r['session_google_ads_campaign_name']}</td><td>{fmt_number(r['sessions'])}</td><td><b style='color:#1D9E75'>{fmt_currency(r['purchase_revenue'])}</b></td><td>{int(r['transactions'])}</td><td><b style='color:{'#1D9E75' if cv>=1 else '#EF9F27' if cv>=0.5 else '#D85A30'}'>{fmt_pct(cv,2)}</b></td><td>{fmt_currency(r['rps'],1)}</td><td>{badge}</td></tr>")
            st.markdown(f"<table class='styled-table'><thead><tr><th>Campaign</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Ses</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        else:
            st.info("مفيش بيانات campaigns كفاية (محتاج أكتر من 100 session).")
    else:
        st.info("مفيش بيانات campaigns متاحة لهذا الفلتر.")

    # ── META CAMPAIGNS ───────────────────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Meta Campaigns", "أداء كامبينز Facebook & Instagram في GA4", "#1877F2"), unsafe_allow_html=True)
    st.caption("البيانات من GA4 عن طريق UTM parameters — session_manual_campaign_name")

    with st.spinner("Loading Meta campaigns..."):
        df_meta = load_meta_campaigns(date_preset, _d_from, _d_to, source_filter)

    if not df_meta.empty and "session_manual_campaign_name" in df_meta.columns:
        for col in ["sessions", "purchase_revenue", "transactions", "add_to_carts"]:
            if col in df_meta.columns:
                df_meta[col] = df_meta[col].apply(safe_num)
        df_meta_agg = df_meta.groupby("session_manual_campaign_name").sum(numeric_only=True).reset_index()

        exclude = ["(organic)", "(not set)", "(referral)", "(direct)"]
        df_meta_f = df_meta_agg[
            ~df_meta_agg["session_manual_campaign_name"].isin(exclude) &
            df_meta_agg["session_manual_campaign_name"].notna() &
            (df_meta_agg["sessions"] > 5)
        ].copy()

        if not df_meta_f.empty:
            df_meta_f["cvr"] = df_meta_f.apply(lambda r: r["transactions"] / r["sessions"] * 100 if r["sessions"] > 0 else 0, axis=1)
            df_meta_f["rps"] = df_meta_f.apply(lambda r: r["purchase_revenue"] / r["sessions"] if r["sessions"] > 0 else 0, axis=1)
            df_meta_f["aov"] = df_meta_f.apply(lambda r: r["purchase_revenue"] / r["transactions"] if r["transactions"] > 0 else 0, axis=1)
            df_meta_f = df_meta_f.sort_values("purchase_revenue", ascending=False)

            tot_meta_rev = df_meta_f["purchase_revenue"].sum()
            tot_meta_ses = df_meta_f["sessions"].sum()
            tot_meta_ord = df_meta_f["transactions"].sum()
            meta_cvr = tot_meta_ord / tot_meta_ses * 100 if tot_meta_ses > 0 else 0
            meta_aov = tot_meta_rev / tot_meta_ord if tot_meta_ord > 0 else 0

            mk1, mk2, mk3, mk4 = st.columns(4)
            with mk1: st.markdown(kpi_card("Meta Revenue", fmt_currency(tot_meta_rev), "via UTM campaigns", "up", accent_color="#1877F2"), unsafe_allow_html=True)
            with mk2: st.markdown(kpi_card("Meta Sessions", fmt_number(tot_meta_ses), "من كل الكامبينز", "neu", accent_color="#1877F2"), unsafe_allow_html=True)
            with mk3: st.markdown(kpi_card("Meta Orders", fmt_number(tot_meta_ord), f"CVR: {fmt_pct(meta_cvr,2)}", "up" if meta_cvr > 0.5 else "warn", accent_color="#1877F2"), unsafe_allow_html=True)
            with mk4: st.markdown(kpi_card("Meta AOV", fmt_currency(meta_aov, 0), "متوسط قيمة الطلب", "neu", accent_color="#1877F2"), unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            rows = []
            for _, r in df_meta_f.head(20).iterrows():
                cv = r["cvr"]
                badge = '<span class="badge badge-green">الأقوى</span>' if cv >= 1 else ('<span class="badge badge-amber">راجع</span>' if cv >= 0.4 else '<span class="badge badge-red">ضعيف</span>')
                rows.append(f"<tr><td style='font-size:11px'>{r['session_manual_campaign_name']}</td><td>{fmt_number(r['sessions'])}</td><td><b style='color:#1877F2'>{fmt_currency(r['purchase_revenue'])}</b></td><td>{int(r['transactions'])}</td><td>{fmt_pct(cv,2)}</td><td>{fmt_currency(r['aov'],0)}</td><td>{badge}</td></tr>")
            st.markdown(f"<table class='styled-table'><thead><tr><th>Campaign</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        else:
            st.info("مفيش بيانات Meta campaigns كفاية حالياً.")
    else:
        st.info("مفيش بيانات Meta campaigns متاحة — تأكد إن UTM parameters متظبطة صح.")
