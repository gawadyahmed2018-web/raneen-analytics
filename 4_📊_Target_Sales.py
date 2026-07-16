"""
Target & Sales Overview Dashboard
----------------------------------
Interactive Streamlit dashboard for daily marketing spend vs. sales targets.

Data is pulled live on every load (cached for 10 minutes) from the published
Google Sheet CSV export. No local data file is needed.

Run locally with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Target & Sales Overview",
    page_icon="📊",
    layout="wide",
)

# رابط الشيت المنشور (Publish to web) — بيتحوّل تلقائيًا لصيغة تصدير CSV
SHEET_ID = "2PACX-1vToNIxR30TywAr5X3Ok7EOtRoMVnHGttVb6AxUZpkUT8161rVVGCIZ542n9K_SEjsAzGo3yWFUuTuUr"
SHEET_GID = "559443792"
SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/e/{SHEET_ID}/pub"
    f"?gid={SHEET_GID}&single=true&output=csv"
)

# --------------------------------------------------------------------------
# Data loading & cleaning
# --------------------------------------------------------------------------
NUMERIC_COLS = [
    "Dollar Rate", "Facebook Spending (USD)", "Facebook Spending",
    "Google Base Amount (USD)", "Google Extra Amount", "Google Spending",
    "SMS Spending", "TikTok Spending", "Criteo Spending", "Extra Spending",
    "Coupons", "Total Spending", "Spending Target", "Received Sales",
    "Received Target", "Confirmed Sales", "Confirmed Target",
    "Retail Confirmed Sales", "Retail Confirmed Target",
    "Marketplace Confirmed Sales", "Marketplace Confirmed Target",
    "Saved Spending", "No. of Orders", "AOV", "Days Remaining Each Month",
    "NumberOfOrdersRetail.Confirmed", "NumberOfOrdersRetail.Confirmed.Target",
    "NumberOfOrdersMarketplace.Confirmed",
    "NumberOfOrdersMarketplace.Confirmed.Target",
    "Number ofQTYRetail", "Number of QTYMarketplace", "PV.Web", "PV.APP",
]

SPEND_CHANNELS = {
    "Facebook Spending": "Facebook",
    "Google Spending": "Google",
    "SMS Spending": "SMS",
    "TikTok Spending": "TikTok",
    "Criteo Spending": "Criteo",
    "Extra Spending": "Extra",
    "Coupons": "Coupons",
}


@st.cache_data(ttl=600, show_spinner="بيتم تحميل البيانات من الشيت...")
def load_data(source) -> pd.DataFrame:
    df = pd.read_csv(source)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            )
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    # Rows with no actual spend/sales recorded are just future placeholder
    # rows in the sheet (dates that haven't happened yet) — drop them.
    has_activity = (df["Total Spending"].fillna(0) > 0) | (df["Received Sales"].fillna(0) > 0)
    if has_activity.any():
        last_real_date = df.loc[has_activity, "Date"].max()
        df = df[df["Date"] <= last_real_date].reset_index(drop=True)

    df["Spending Achievement %"] = (df["Total Spending"] / df["Spending Target"] * 100)
    df["Confirmed Achievement %"] = (df["Confirmed Sales"] / df["Confirmed Target"] * 100)
    df["Received Achievement %"] = (df["Received Sales"] / df["Received Target"] * 100)
    return df


title_col, refresh_col = st.columns([6, 1])
with title_col:
    st.title("📊 Target & Sales Overview")
with refresh_col:
    st.write("")
    if st.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

try:
    df = load_data(SHEET_CSV_URL)
except Exception as e:
    st.error(f"تعذر تحميل البيانات من الشيت مباشرةً: {e}")
    st.info("تأكد إن الشيت لسه published to web، أو ارفع نسخة CSV يدويًا كبديل مؤقت.")
    uploaded = st.file_uploader("ارفع ملف CSV", type=["csv"])
    if uploaded is None:
        st.stop()
    df = load_data(uploaded)

# --------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------
st.sidebar.header("🔎 الفلاتر")

min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
default_start = max(min_date, (df["Date"].max() - pd.Timedelta(days=90)).date())

date_range = st.sidebar.date_input(
    "الفترة الزمنية",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

granularity = st.sidebar.radio("التجميع الزمني", ["يومي", "أسبوعي", "شهري"], index=2)

mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
fdf = df.loc[mask].copy()

if fdf.empty:
    st.info("لا توجد بيانات في الفترة المختارة.")
    st.stop()

freq_map = {"يومي": "D", "أسبوعي": "W", "شهري": "MS"}
freq = freq_map[granularity]


def resample_sum(frame: pd.DataFrame, cols: list) -> pd.DataFrame:
    return frame.set_index("Date")[cols].resample(freq).sum(min_count=1).reset_index()


# --------------------------------------------------------------------------
# KPI cards
# --------------------------------------------------------------------------
total_spend = fdf["Total Spending"].sum()
spend_target = fdf["Spending Target"].sum()
confirmed_sales = fdf["Confirmed Sales"].sum()
confirmed_target = fdf["Confirmed Target"].sum()
received_sales = fdf["Received Sales"].sum()
received_target = fdf["Received Target"].sum()
saved_spend = fdf["Saved Spending"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "إجمالي الإنفاق",
    f"{total_spend:,.0f}",
    f"{total_spend - spend_target:,.0f} vs. التارجت",
)
col2.metric(
    "المبيعات المؤكدة (Confirmed)",
    f"{confirmed_sales:,.0f}",
    f"{(confirmed_sales/confirmed_target*100 - 100):.1f}% vs. التارجت" if confirmed_target else "N/A",
)
col3.metric(
    "المبيعات المستلمة (Received)",
    f"{received_sales:,.0f}",
    f"{(received_sales/received_target*100 - 100):.1f}% vs. التارجت" if received_target else "N/A",
)
col4.metric(
    "الإنفاق الموفّر (Saved)",
    f"{saved_spend:,.0f}",
)

col5, col6, col7, col8 = st.columns(4)
retail_sales = fdf["Retail Confirmed Sales"].sum()
retail_target = fdf["Retail Confirmed Target"].sum()
mp_sales = fdf["Marketplace Confirmed Sales"].sum()
mp_target = fdf["Marketplace Confirmed Target"].sum()
orders = fdf["No. of Orders"].sum()
avg_aov = fdf["AOV"].mean()

col5.metric("مبيعات Retail المؤكدة", f"{retail_sales:,.0f}",
            f"{(retail_sales/retail_target*100 - 100):.1f}% vs. التارجت" if retail_target else "N/A")
col6.metric("مبيعات Marketplace المؤكدة", f"{mp_sales:,.0f}",
            f"{(mp_sales/mp_target*100 - 100):.1f}% vs. التارجت" if mp_target else "N/A")
col7.metric("عدد الأوردرات", f"{orders:,.0f}" if orders else "لا توجد بيانات")
col8.metric("متوسط قيمة الطلب (AOV)", f"{avg_aov:,.0f}" if pd.notna(avg_aov) else "لا توجد بيانات")

st.divider()

# --------------------------------------------------------------------------
# Spending vs Target trend
# --------------------------------------------------------------------------
st.subheader("الإنفاق مقابل التارجت")
spend_trend = resample_sum(fdf, ["Total Spending", "Spending Target"])
fig_spend = go.Figure()
fig_spend.add_trace(go.Bar(x=spend_trend["Date"], y=spend_trend["Total Spending"], name="الإنفاق الفعلي"))
fig_spend.add_trace(go.Scatter(x=spend_trend["Date"], y=spend_trend["Spending Target"], name="التارجت",
                                mode="lines+markers", line=dict(color="crimson", width=3)))
fig_spend.update_layout(barmode="group", hovermode="x unified", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig_spend, use_container_width=True)

# --------------------------------------------------------------------------
# Confirmed / Received Sales vs Target
# --------------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("المبيعات المؤكدة مقابل التارجت")
    conf_trend = resample_sum(fdf, ["Confirmed Sales", "Confirmed Target"])
    fig_conf = go.Figure()
    fig_conf.add_trace(go.Bar(x=conf_trend["Date"], y=conf_trend["Confirmed Sales"], name="المؤكد فعلياً"))
    fig_conf.add_trace(go.Scatter(x=conf_trend["Date"], y=conf_trend["Confirmed Target"], name="التارجت",
                                   mode="lines+markers", line=dict(color="crimson", width=3)))
    fig_conf.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_conf, use_container_width=True)

with c2:
    st.subheader("المبيعات المستلمة مقابل التارجت")
    recv_trend = resample_sum(fdf, ["Received Sales", "Received Target"])
    fig_recv = go.Figure()
    fig_recv.add_trace(go.Bar(x=recv_trend["Date"], y=recv_trend["Received Sales"], name="المستلم فعلياً"))
    fig_recv.add_trace(go.Scatter(x=recv_trend["Date"], y=recv_trend["Received Target"], name="التارجت",
                                   mode="lines+markers", line=dict(color="crimson", width=3)))
    fig_recv.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_recv, use_container_width=True)

# --------------------------------------------------------------------------
# Retail vs Marketplace
# --------------------------------------------------------------------------
st.subheader("Retail مقابل Marketplace (مبيعات مؤكدة)")
rm_trend = resample_sum(fdf, ["Retail Confirmed Sales", "Marketplace Confirmed Sales",
                               "Retail Confirmed Target", "Marketplace Confirmed Target"])
fig_rm = go.Figure()
fig_rm.add_trace(go.Bar(x=rm_trend["Date"], y=rm_trend["Retail Confirmed Sales"], name="Retail فعلي"))
fig_rm.add_trace(go.Bar(x=rm_trend["Date"], y=rm_trend["Marketplace Confirmed Sales"], name="Marketplace فعلي"))
fig_rm.update_layout(barmode="stack", hovermode="x unified", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig_rm, use_container_width=True)

# --------------------------------------------------------------------------
# Spending breakdown by channel
# --------------------------------------------------------------------------
st.subheader("توزيع الإنفاق حسب القناة")
available_channels = {k: v for k, v in SPEND_CHANNELS.items() if k in fdf.columns}
channel_totals = fdf[list(available_channels.keys())].sum().rename(index=available_channels)
channel_totals = channel_totals[channel_totals > 0].sort_values(ascending=False)

cc1, cc2 = st.columns([1, 1])
with cc1:
    fig_pie = px.pie(names=channel_totals.index, values=channel_totals.values, hole=0.45)
    fig_pie.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

with cc2:
    channel_trend = resample_sum(fdf, list(available_channels.keys())).rename(columns=available_channels)
    channel_trend_long = channel_trend.melt(id_vars="Date", var_name="القناة", value_name="الإنفاق")
    fig_area = px.area(channel_trend_long, x="Date", y="الإنفاق", color="القناة")
    fig_area.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_area, use_container_width=True)

# --------------------------------------------------------------------------
# Orders & AOV (only if data exists)
# --------------------------------------------------------------------------
if fdf["No. of Orders"].notna().any():
    st.subheader("عدد الأوردرات ومتوسط قيمة الطلب (AOV)")
    oc1, oc2 = st.columns(2)
    orders_trend = resample_sum(fdf, ["No. of Orders"])
    aov_trend = fdf.set_index("Date")["AOV"].resample(freq).mean().reset_index()

    with oc1:
        fig_orders = px.bar(orders_trend, x="Date", y="No. of Orders")
        fig_orders.update_layout(hovermode="x unified")
        st.plotly_chart(fig_orders, use_container_width=True)
    with oc2:
        fig_aov = px.line(aov_trend, x="Date", y="AOV", markers=True)
        fig_aov.update_layout(hovermode="x unified")
        st.plotly_chart(fig_aov, use_container_width=True)

# --------------------------------------------------------------------------
# Achievement % heat table (monthly)
# --------------------------------------------------------------------------
st.subheader("نسبة تحقيق التارجت شهرياً")
monthly = fdf.set_index("Date")[[
    "Total Spending", "Spending Target", "Confirmed Sales", "Confirmed Target",
    "Received Sales", "Received Target",
]].resample("MS").sum(min_count=1)
monthly["Spending %"] = (monthly["Total Spending"] / monthly["Spending Target"] * 100).round(1)
monthly["Confirmed %"] = (monthly["Confirmed Sales"] / monthly["Confirmed Target"] * 100).round(1)
monthly["Received %"] = (monthly["Received Sales"] / monthly["Received Target"] * 100).round(1)
monthly.index = monthly.index.strftime("%Y-%m")

st.dataframe(
    monthly[["Spending %", "Confirmed %", "Received %"]].style.background_gradient(
        cmap="RdYlGn", vmin=70, vmax=130, axis=None
    ),
    use_container_width=True,
)

st.divider()

# --------------------------------------------------------------------------
# Raw data table + download
# --------------------------------------------------------------------------
with st.expander("📄 عرض البيانات التفصيلية (الفترة المختارة)"):
    st.dataframe(fdf, use_container_width=True)
    st.download_button(
        "تحميل البيانات المفلترة (CSV)",
        data=fdf.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"filtered_data_{start_date}_{end_date}.csv",
        mime="text/csv",
    )

st.caption(f"آخر تحديث للبيانات: {df['Date'].max().date()} — عدد الأيام في الملف: {len(df)}")
