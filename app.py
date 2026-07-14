import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io

st.set_page_config(page_title="Raneen Sales Dashboard", layout="wide", page_icon="📊")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f8f9fa; }
[data-testid="stSidebar"] { background: #1F3864; }
[data-testid="stSidebar"] * { color: white !important; }
.metric-card {
    background: white; border-radius: 10px; padding: 1rem 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: .5rem;
}
.metric-label { font-size: 12px; color: #888; margin: 0 0 4px; }
.metric-value { font-size: 22px; font-weight: 600; color: #1F3864; margin: 0; }
.metric-sub { font-size: 11px; color: #aaa; margin: 2px 0 0; }
.section-title {
    font-size: 13px; font-weight: 600; color: #1F3864;
    text-transform: uppercase; letter-spacing: .06em;
    border-bottom: 2px solid #1F3864; padding-bottom: 6px;
    margin: 2rem 0 1rem;
}
[data-testid="stDownloadButton"] > button {
    background: #1F3864 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 6px 14px !important;
    transition: background .2s !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #2a4f8a !important;
    color: white !important;
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input {
    background: #eef3fb !important;
    border: 1.5px solid #3266ad !important;
    border-radius: 8px !important;
    color: #1F3864 !important;
    font-weight: 500 !important;
}
[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label {
    color: #1F3864 !important;
    font-weight: 600 !important;
    font-size: 12px !important;
}
.tbl-header th {
    background: #1F3864 !important;
    color: white !important;
    font-weight: 600 !important;
}
.pct-bold { font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

def to_excel(df_export):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Sheet1")
    return buf.getvalue()

COLORS = {"raneen": "#3266ad", "MP": "#d85a30"}
PAL = ["#3266ad","#185fa5","#378add","#85b7eb","#d85a30","#ba7517","#2a9e75","#533ab7","#993556","#2c2c2a"]

def clean_money(s):
    return pd.to_numeric(
        s.astype(str).str.replace("EGP","",regex=False).str.replace(",","",regex=False).str.strip(),
        errors="coerce"
    ).fillna(0)

@st.cache_data(max_entries=1)
def process(file):
    df = pd.read_csv(file)
    df = df[df["Purchase Point"].str.contains("Raneen", na=False)].copy()
    df = df[~df["Order Status"].isin(["Canceled","Failed Payment"])].copy()
    for col in ["Item Price","Discount Amount","Marketing Discount","Commercial Discount","Row Total"]:
        df[col] = clean_money(df[col])
    df["Value After Discounts"] = df["Row Total"] - df["Discount Amount"]
    df["Seller_Raw"] = df["Marketplace Seller"].apply(
        lambda x: "raneen" if pd.isna(x) or str(x).strip()=="" else str(x).strip()
    )
    df["Marketplace Seller"] = df["Marketplace Seller"].apply(
        lambda x: "raneen" if pd.isna(x) or str(x).strip()==""  else "MP"
    )
    df["Purchase Date"] = pd.to_datetime(df["Purchase Date"], format="%b %d, %Y, %I:%M:%S %p", errors="coerce")
    df["Day"] = df["Purchase Date"].dt.strftime("%b %d")
    # Keep only needed columns
    _keep_cols = [
        "Order #", "Purchase Date", "Day",
        "Marketplace Seller", "Seller_Raw", "Attribute Set", "Name", "SKU",
        "Qty Ordered", "Item Price", "Row Total", "Discount Amount",
        "Value After Discounts", "Coupon Code", "Customer Region", "Payment Method"
    ]
    df = df[[c for c in _keep_cols if c in df.columns]].copy()
    # Optimize dtypes — saves ~50% memory
    for _col in ["Qty Ordered","Item Price","Row Total","Discount Amount","Value After Discounts"]:
        if _col in df.columns:
            df[_col] = pd.to_numeric(df[_col], errors="coerce").astype("float32")
    for _col in ["Attribute Set","Marketplace Seller","Customer Region","Payment Method"]:
        if _col in df.columns:
            df[_col] = df[_col].astype("category")
    return df


# ── RANEEN VS MP ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">Raneen vs MP — مبيعات يومية</p>', unsafe_allow_html=True)

daily_r   = df[df["Marketplace Seller"]=="raneen"].groupby("Day")["Value After Discounts"].sum()
daily_mp  = df[df["Marketplace Seller"]=="MP"].groupby("Day")["Value After Discounts"].sum()
daily_tot = df.groupby("Day")["Value After Discounts"].sum()

r_vals   = [daily_r.get(d, 0)  for d in days_sorted]
mp_vals  = [daily_mp.get(d, 0) for d in days_sorted]
tot_vals = [daily_tot.get(d, 0) for d in days_sorted]

fig_ts = go.Figure()
fig_ts.add_trace(go.Scatter(
    x=days_sorted, y=r_vals, name="Raneen",
    mode="lines+markers", line=dict(color="#3266ad", width=2.5),
    marker=dict(size=6),
    hovertemplate="<b>%{x}</b><br>Raneen: %{y:,.0f} ج<extra></extra>"
))
fig_ts.add_trace(go.Scatter(
    x=days_sorted, y=mp_vals, name="MP",
    mode="lines+markers", line=dict(color="#d85a30", width=2.5),
    marker=dict(size=6),
    hovertemplate="<b>%{x}</b><br>MP: %{y:,.0f} ج<extra></extra>"
))
fig_ts.add_trace(go.Scatter(
    x=days_sorted, y=tot_vals, name="الإجمالي",
    mode="lines+markers", line=dict(color="#2a9e75", width=2, dash="dot"),
    marker=dict(size=5),
    hovertemplate="<b>%{x}</b><br>الإجمالي: %{y:,.0f} ج<extra></extra>"
))

for i, day in enumerate(days_sorted):
    tot = tot_vals[i]
    if tot > 0:
        r_pct = r_vals[i] / tot * 100
        mp_pct = mp_vals[i] / tot * 100

# Spend line intentionally removed for performance

fig_ts.update_layout(
    height=320,
    margin=dict(t=20, b=20, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(tickformat=",.0f", gridcolor="rgba(128,128,128,0.1)"),

    xaxis=dict(showgrid=False),
    hovermode="x unified"
)
st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})

# Orders/AOV/Qty chart removed for performance

# ── MAIN CATEGORY METRICS ────────────────────────────────────────────────────
st.markdown('<p class="section-title">أداء الـ Main Categories</p>', unsafe_allow_html=True)

_mc_summary = df.groupby("Main Category")["Value After Discounts"].sum().sort_values(ascending=False)
_mc_total   = _mc_summary.sum()
_mc_colors  = ["#3266ad","#d85a30","#2a9e75","#ba7517","#533ab7","#993556","#185fa5","#639922","#854f0b"]
_mc_list    = _mc_summary.index.tolist()

_mc_raneen = df[df["Marketplace Seller"]=="raneen"].groupby("Main Category")["Value After Discounts"].sum()
_mc_mp     = df[df["Marketplace Seller"]=="MP"].groupby("Main Category")["Value After Discounts"].sum()

_mc_cols = st.columns(len(_mc_list))
for _i, (_mc_name, _mc_rev) in enumerate(_mc_summary.items()):
    _mc_pct = _mc_rev / _mc_total * 100 if _mc_total > 0 else 0
    _mc_col = _mc_colors[_i % len(_mc_colors)]
    _r_rev  = _mc_raneen.get(_mc_name, 0)
    _m_rev  = _mc_mp.get(_mc_name, 0)
    _r_pct  = _r_rev / _mc_rev * 100 if _mc_rev > 0 else 0
    _m_pct  = _m_rev / _mc_rev * 100 if _mc_rev > 0 else 0
    _bar = (
        f"<div style='margin-top:6px'>"
        f"<div style='display:flex;height:7px;border-radius:4px;overflow:hidden'>"
        f"<div style='width:{_r_pct:.0f}%;background:#3266ad'></div>"
        f"<div style='width:{_m_pct:.0f}%;background:#d85a30'></div>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;margin-top:3px'>"
        f"<span style='font-size:9px;color:#3266ad;font-weight:600'>R {_r_pct:.0f}%</span>"
        f"<span style='font-size:9px;color:#d85a30;font-weight:600'>MP {_m_pct:.0f}%</span>"
        f"</div></div>"
    )
    with _mc_cols[_i]:
        st.markdown(
            f'<div class="metric-card" style="border-left:4px solid {_mc_col};padding:.65rem .9rem">' +
            f'<p class="metric-label" style="font-size:11px">{_mc_name}</p>' +
            f'<p class="metric-value" style="color:{_mc_col};font-size:17px">{_mc_rev/1e6:.2f}M</p>' +
            f'<p class="metric-sub">{_mc_pct:.1f}% من الإجمالي</p>' +
            _bar +
            '</div>',
            unsafe_allow_html=True
        )

# ── BY CATEGORY ───────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">مبيعات كل قسم — Raneen vs MP</p>', unsafe_allow_html=True)

# Main Category filter
_sel_main_cat = st.selectbox(
    "فلتر بـ Main Category",
    ["كل الأقسام"] + _mc_list,
    key="main_cat_filter",
    label_visibility="collapsed"
)

_df_for_cat = df.copy()
if _sel_main_cat != "كل الأقسام":
    _df_for_cat = _df_for_cat[_df_for_cat["Main Category"] == _sel_main_cat]

cat_all = _df_for_cat.groupby(["Attribute Set","Marketplace Seller"])["Value After Discounts"].sum().unstack(fill_value=0).reset_index()
if "MP" not in cat_all.columns: cat_all["MP"]=0
if "raneen" not in cat_all.columns: cat_all["raneen"]=0
cat_all["Total"] = cat_all["MP"] + cat_all["raneen"]
cat_all["Channel"] = cat_all.apply(lambda r: "Raneen Only" if r["MP"]==0 else ("MP Only" if r["raneen"]==0 else "Both"), axis=1)
cat_all = cat_all.sort_values("Total", ascending=False)
cat_all["Attribute Set"] = cat_all["Attribute Set"].str.replace("&amp;","&")

col_f1, col_f2 = st.columns([2,1])
with col_f1:
    search_cat = st.text_input("ابحث باسم القسم", placeholder="مثال: Air Conditioner", label_visibility="collapsed")
with col_f2:
    channel_filter = st.selectbox("فلتر القسم", ["كل الأقسام","Raneen + MP معاً","Raneen فقط","MP فقط"], label_visibility="collapsed")

cat_ch = cat_all.copy()
if search_cat:
    cat_ch = cat_ch[cat_ch["Attribute Set"].str.lower().str.contains(search_cat.lower())]
if channel_filter == "Raneen + MP معاً":
    cat_ch = cat_ch[(cat_ch["raneen"]>0) & (cat_ch["MP"]>0)]
elif channel_filter == "Raneen فقط":
    cat_ch = cat_ch[(cat_ch["raneen"]>0) & (cat_ch["MP"]==0)]
elif channel_filter == "MP فقط":
    cat_ch = cat_ch[(cat_ch["MP"]>0) & (cat_ch["raneen"]==0)]

_dl_col1, _dl_col2 = st.columns([3,1])
with _dl_col1:
    st.caption(f"عرض {len(cat_ch)} من {len(cat_all)} قسم — الشارت بيعرض أعلى 12 من النتايج")
with _dl_col2:
    _cat_csv = cat_ch[["Attribute Set","Channel","raneen","MP","Total"]].rename(columns={"Attribute Set":"القسم","raneen":"Raneen (ج)","MP":"MP (ج)","Total":"الإجمالي (ج)","Channel":"Channel"})
    st.download_button("⬇ تصدير Excel", to_excel(_cat_csv), "مبيعات_الأقسام.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

fig_cat = go.Figure()
chart_data = cat_ch.head(12)
fig_cat.add_trace(go.Bar(name="Raneen", y=chart_data["Attribute Set"], x=chart_data["raneen"],
    orientation="h", marker_color="#3266ad", hovertemplate="%{x:,.0f} ج<extra>Raneen</extra>"))
fig_cat.add_trace(go.Bar(name="MP", y=chart_data["Attribute Set"], x=chart_data["MP"],
    orientation="h", marker_color="#d85a30", hovertemplate="%{x:,.0f} ج<extra>MP</extra>"))
fig_cat.update_layout(barmode="group", height=max(320, len(chart_data)*38),
    margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02), xaxis=dict(tickformat=",.0f"))
st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})

max_total = cat_ch["Total"].max() if len(cat_ch) > 0 else 1
cat_html = """<div style='max-height:520px;overflow-y:auto'><table style='width:100%;border-collapse:collapse;font-size:12px'>
<tr style='border-bottom:1.5px solid #1F3864;position:sticky;top:0;background:#1F3864;z-index:2'>
<th style='padding:7px 8px;text-align:left;color:white;font-size:11px'>#</th>
<th style='padding:7px 8px;text-align:left;color:white;font-size:11px'>القسم</th>
<th style='padding:7px 8px;text-align:left;color:white;font-size:11px'>Channel</th>
<th style='padding:7px 8px;text-align:right;color:#85b7eb;font-size:11px'>Raneen (ج)</th>
<th style='padding:7px 8px;text-align:right;color:#f0997b;font-size:11px'>MP (ج)</th>
<th style='padding:7px 8px;text-align:right;color:white;font-size:11px'>الإجمالي (ج)</th>
<th style='padding:7px 8px;color:white;font-size:11px;min-width:160px'>Raneen vs MP</th>
</tr>"""
for i, (_, row) in enumerate(cat_ch.iterrows(), 1):
    tot = row["Total"] if row["Total"] > 0 else 1
    r_pct = row["raneen"] / tot * 100
    m_pct = row["MP"] / tot * 100
    bar_w = row["Total"] / max_total * 100
    ch = row["Channel"]
    ch_color = "#3266ad" if ch=="Raneen Only" else "#d85a30" if ch=="MP Only" else "#2a9e75"
    ch_bg    = "#e6f1fb" if ch=="Raneen Only" else "#fcebeb" if ch=="MP Only" else "#e1f5ee"
    split_bar = f"""<div style='display:flex;height:8px;border-radius:4px;overflow:hidden;width:{bar_w:.0f}%;min-width:4px'>
<div style='width:{r_pct:.0f}%;background:#3266ad'></div>
<div style='width:{m_pct:.0f}%;background:#d85a30'></div>
</div>
<div style='font-size:10px;color:#aaa;margin-top:2px'><b>{r_pct:.0f}%</b> Raneen · <b>{m_pct:.0f}%</b> MP</div>"""
    cat_html += f"""<tr style='border-bottom:.5px solid #f0f0f0'>
<td style='padding:6px 8px;color:#aaa'>{i}</td>
<td style='padding:6px 8px;font-weight:{"500" if i<=5 else "400"}'>{row["Attribute Set"]}</td>
<td style='padding:6px 8px'><span style='background:{ch_bg};color:{ch_color};font-size:10px;padding:1px 6px;border-radius:6px;font-weight:500'>{ch}</span></td>
<td style='padding:6px 8px;text-align:right;color:#3266ad'>{row["raneen"]:,.0f}</td>
<td style='padding:6px 8px;text-align:right;color:#d85a30'>{row["MP"]:,.0f}</td>
<td style='padding:6px 8px;text-align:right;font-weight:500'>{row["Total"]:,.0f}</td>
<td style='padding:6px 8px'>{split_bar}</td>
</tr>"""
cat_html += "</table></div>"
st.markdown(cat_html, unsafe_allow_html=True)

st.markdown('<p class="section-title">مبيعات يومية — أعلى 6 أقسام</p>', unsafe_allow_html=True)

_lf1, _lf2 = st.columns([1, 1])
with _lf1:
    _line_main_cats = sorted(df["Main Category"].dropna().unique().tolist())
    _line_main_sel  = st.multiselect("فلتر بـ Main Category", _line_main_cats, placeholder="كل الأقسام", key="line_main", label_visibility="collapsed")
with _lf2:
    _df_line = df.copy()
    if _line_main_sel:
        _df_line = _df_line[_df_line["Main Category"].isin(_line_main_sel)]
    _line_attr_cats = sorted(_df_line["Attribute Set"].dropna().unique().tolist())
    _line_attr_sel  = st.multiselect("فلتر بـ Attribute Set", _line_attr_cats, placeholder="كل الأقسام", key="line_attr", label_visibility="collapsed")

if _line_attr_sel:
    _df_line = _df_line[_df_line["Attribute Set"].isin(_line_attr_sel)]

top6_cats = _df_line.groupby("Attribute Set")["Value After Discounts"].sum().nlargest(6).index.tolist()

# ألوان متباينة بشكل واضح
DISTINCT_COLORS = [
    "#2563eb",  # أزرق غامق
    "#e63946",  # أحمر
    "#2a9e75",  # أخضر
    "#f4a621",  # برتقالي/ذهبي
    "#9333ea",  # بنفسجي
    "#0ea5e9",  # سماوي
    "#ef4444",  # أحمر فاتح
    "#16a34a",  # أخضر غامق
    "#f59e0b",  # عنبر
    "#6366f1",  # بنفسجي فاتح
]

DASH_STYLES = ["solid","dot","dash","dashdot","longdash","solid","dot","dash","dashdot","longdash"]
MARKER_SYMBOLS = ["circle","square","diamond","triangle-up","cross","star","circle","square","diamond","triangle-up"]

fig_line = go.Figure()
for i, cat in enumerate(top6_cats):
    cat_data = _df_line[_df_line["Attribute Set"]==cat].groupby("Day")["Value After Discounts"].sum()
    vals = [cat_data.get(d,0) for d in days_sorted]
    cat_clean = cat.replace("&amp;","&")
    fig_line.add_trace(go.Scatter(
        x=days_sorted, y=vals,
        name=cat_clean,
        mode="lines+markers",
        line=dict(color=DISTINCT_COLORS[i % len(DISTINCT_COLORS)], width=2.5, dash=DASH_STYLES[i % len(DASH_STYLES)]),
        marker=dict(size=7, symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                    color=DISTINCT_COLORS[i % len(DISTINCT_COLORS)],
                    line=dict(width=1.5, color="white")),
        hovertemplate=(
            "<span style='font-size:14px;font-weight:700'>" + cat_clean + "</span><br>"
            "<b>%{x}</b><br>"
            "المبيعات: <b>%{y:,.0f} ج</b>"
            "<extra></extra>"
        )
    ))
fig_line.update_layout(
    height=340,
    margin=dict(t=10,b=10,l=10,r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=12)),
    yaxis=dict(tickformat=",.0f", gridcolor="rgba(128,128,128,0.1)"),
    xaxis=dict(showgrid=False),
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="sans-serif",
                    bordercolor="rgba(0,0,0,0.1)"),
    hovermode="x unified"
)
st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

# ── TOP PRODUCTS with heatbar ────────────────────────────────────────────────
st.markdown('<p class="section-title">أعلى المنتجات طلبًا</p>', unsafe_allow_html=True)

_col_tp1, _col_tp2, _col_tp3 = st.columns([1,1,1])
with _col_tp1:
    _all_cats_tp = ["كل الأقسام"] + sorted(df["Attribute Set"].dropna().unique().tolist())
    _sel_cat_tp = st.selectbox("فلتر بالقسم", _all_cats_tp, key="tp_cat_filter", label_visibility="collapsed")
with _col_tp2:
    _max_days_tp = len(days_sorted)
    _days_options = ["كل الأيام"] + [str(d) for d in range(1, _max_days_tp + 1)]
    _sel_days_tp = st.selectbox(
        "فلتر بعدد أيام النشاط (على الأقل)",
        _days_options, key="tp_days_filter", label_visibility="collapsed"
    )
with _col_tp3:
    _perf_options = ["كل المنتجات", "⭐ ممتاز (90%+)", "✅ جيد (80–90%)", "🔶 متوسط (70–80%)", "🔴 ضعيف (أقل من 70%)"]
    _sel_perf_tp = st.selectbox("فلتر بمعيار الأداء", _perf_options, key="tp_perf_filter", label_visibility="collapsed")

_df_tp = df.copy()
if _sel_main_cat != "كل الأقسام":
    _df_tp = _df_tp[_df_tp["Main Category"] == _sel_main_cat]
if _sel_cat_tp != "كل الأقسام":
    _df_tp = _df_tp[_df_tp["Attribute Set"] == _sel_cat_tp]

top_prod = _df_tp.groupby("Name").agg(
    SKU=("SKU","first"),
    Qty=("Qty Ordered","sum"),
    Revenue=("Value After Discounts","sum"),
    Days=("Day","nunique")
).sort_values("Qty", ascending=False)

if _sel_days_tp != "كل الأيام":
    _min_days = int(_sel_days_tp)
    top_prod = top_prod[top_prod["Days"] >= _min_days]

total_d = len(days_sorted)
top_prod["Pct"] = (top_prod["Days"] / total_d * 100).round(1) if total_d > 0 else 0

if _sel_perf_tp == "⭐ ممتاز (90%+)":
    top_prod = top_prod[top_prod["Pct"] >= 90]
elif _sel_perf_tp == "✅ جيد (80–90%)":
    top_prod = top_prod[(top_prod["Pct"] >= 80) & (top_prod["Pct"] < 90)]
elif _sel_perf_tp == "🔶 متوسط (70–80%)":
    top_prod = top_prod[(top_prod["Pct"] >= 70) & (top_prod["Pct"] < 80)]
elif _sel_perf_tp == "🔴 ضعيف (أقل من 70%)":
    top_prod = top_prod[top_prod["Pct"] < 70]

top_prod_all = top_prod.reset_index()  # كل المنتجات للتصدير
top_prod = top_prod.head(20).reset_index()  # أول 20 للعرض

def _perf_style(pct):
    if pct >= 90:
        return {"bg": "#e6f9f0", "color": "#0a7a4e", "badge_bg": "#0a7a4e", "label": "ممتاز ⭐"}
    elif pct >= 80:
        return {"bg": "#e8f4fd", "color": "#1a5fa8", "badge_bg": "#1a5fa8", "label": "جيد ✅"}
    elif pct >= 70:
        return {"bg": "#fff8e6", "color": "#9a6400", "badge_bg": "#ba7517", "label": "متوسط 🔶"}
    else:
        return {"bg": "#fdf0f0", "color": "#b91c1c", "badge_bg": "#d85a30", "label": "ضعيف 🔴"}

max_qty_p = top_prod["Qty"].max() if len(top_prod) > 0 else 1
max_rev_p = top_prod["Revenue"].max() if len(top_prod) > 0 else 1

prod_rows = ""
for idx_p, row_p in top_prod.iterrows():
    qty_w = int(row_p["Qty"] / max_qty_p * 80) if max_qty_p > 0 else 0
    rev_w = int(row_p["Revenue"] / max_rev_p * 80) if max_rev_p > 0 else 0
    days_act = int(row_p["Days"])
    pct_val  = row_p["Pct"]
    ps       = _perf_style(pct_val)
    heat_cells = "".join([
        '<span style="display:inline-block;width:8px;height:8px;border-radius:1px;margin:1px;background:%s"></span>' % (ps["badge_bg"] if j < days_act else "#e0e0e0")
        for j in range(total_d)
    ])
    name_s = str(row_p["Name"])[:50] + ("..." if len(str(row_p["Name"])) > 50 else "")
    pct_cell = (
        f'<div style="background:{ps["bg"]};border-radius:6px;padding:3px 7px;display:inline-block;min-width:90px;text-align:center">'
        f'<span style="font-weight:700;color:{ps["color"]};font-size:13px">{pct_val:.0f}%</span><br>'
        f'<span style="font-size:10px;color:{ps["color"]};opacity:.85">{ps["label"]}</span>'
        f'</div>'
    )
    sku_val = str(row_p.get("SKU","")) if isinstance(row_p, dict) else str(row_p["SKU"]) if "SKU" in top_prod.columns else str(idx_p+1)
    prod_rows += (
        '<tr style="border-bottom:.5px solid #f0f0f0">' +
        '<td style="padding:5px 8px;color:#555;font-family:monospace;font-size:10px;max-width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + sku_val + '">' + sku_val[:15] + ('…' if len(sku_val)>15 else '') + '</td>' +
        '<td style="padding:5px 8px;max-width:200px" title="' + str(row_p["Name"]) + '">' + name_s + '</td>' +
        '<td style="padding:5px 8px;text-align:right"><span style="font-weight:600">' + f'{int(row_p["Qty"]):,}' + '</span>' +
        '<div style="background:#e8f0fb;border-radius:2px;height:4px;margin-top:3px"><div style="width:' + str(qty_w) + '%;background:#3266ad;height:4px;border-radius:2px"></div></div></td>' +
        '<td style="padding:5px 8px;text-align:right">' + f'{row_p["Revenue"]:,.0f}' +
        '<div style="background:#fde8e0;border-radius:2px;height:4px;margin-top:3px"><div style="width:' + str(rev_w) + '%;background:#d85a30;height:4px;border-radius:2px"></div></div></td>' +
        '<td style="padding:5px 8px">' + heat_cells + '<span style="font-size:10px;color:#aaa;margin-right:4px">' + str(days_act) + '/' + str(total_d) + '</span></td>' +
        '<td style="padding:5px 8px;text-align:center">' + pct_cell + '</td></tr>'
    )

prod_html = (
    '<div style="max-height:500px;overflow-y:auto">' +
    '<table style="width:100%;border-collapse:collapse;font-size:12px">' +
    '<tr style="border-bottom:1.5px solid #1F3864;position:sticky;top:0;background:#1F3864;z-index:2">' +
    '<th style="padding:7px 8px;text-align:left;color:white;font-size:11px">SKU</th>' +
    '<th style="padding:7px 8px;text-align:left;color:white;font-size:11px">المنتج</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#b5d4f4;font-size:11px">الكمية</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#f0997b;font-size:11px">المبيعات (ج)</th>' +
    '<th style="padding:7px 8px;color:white;font-size:11px">أيام الظهور</th>' +
    '<th style="padding:7px 8px;text-align:center;color:#9fe1cb;font-size:11px">نسبة الأداء</th></tr>' +
    prod_rows + '</table></div>'
)
st.markdown(prod_html, unsafe_allow_html=True)
_tp_dl = top_prod_all[["SKU","Name","Qty","Revenue","Days","Pct"]].rename(columns={"SKU":"SKU","Name":"المنتج","Qty":"الكمية","Revenue":"المبيعات (ج)","Days":"أيام الظهور","Pct":"نسبة الأداء %"})
st.download_button(f"⬇ تصدير Excel — {len(top_prod_all)} منتج", to_excel(_tp_dl), "أعلى_المنتجات.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.markdown('<p class="section-title">خصومات الكوبونات</p>', unsafe_allow_html=True)

c_df = df[df["Coupon Code"].notna() & (df["Coupon Code"].astype(str).str.strip()!="")].copy()
c_df["Coupon"] = c_df["Coupon Code"].str.strip().str.upper()
coup = c_df.groupby("Coupon").agg(
    Total_Discount=("Discount Amount","sum"),
    Orders=("Order #","nunique")
).sort_values("Total_Discount", ascending=False).head(15).reset_index()
coup = coup[coup["Total_Discount"]>0]
coup_total = coup["Total_Discount"].sum()

col1, col2 = st.columns([1,1])
with col1:
    fig_coup = px.bar(coup, x="Coupon", y="Total_Discount",
        color="Coupon", color_discrete_sequence=PAL,
        text_auto=".3s")
    fig_coup.update_layout(showlegend=False, height=300,
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="", yaxis_title="", yaxis=dict(tickformat=",.0f"))
    fig_coup.update_traces(textposition="outside")
    st.plotly_chart(fig_coup, use_container_width=True, config={"displayModeBar": False})

with col2:
    max_disc_c = coup["Total_Discount"].max()
    coup_rows = ""
    for idx_c, (_, cr) in enumerate(coup.iterrows()):
        pct_c = cr["Total_Discount"]/coup_total*100
        bw_c = int(cr["Total_Discount"]/max_disc_c*100) if max_disc_c > 0 else 0
        col_c = PAL[idx_c % len(PAL)]
        coup_rows += (
            '<tr style="border-bottom:.5px solid #f0f0f0">' +
            '<td style="padding:5px 8px;font-weight:600;color:' + col_c + ';font-family:monospace">' + str(cr["Coupon"]) + '</td>' +
            '<td style="padding:5px 8px;text-align:right;font-weight:500">' + f'{cr["Total_Discount"]:,.0f}' + '</td>' +
            '<td style="padding:5px 8px;text-align:right;color:#555">' + str(cr["Orders"]) + '</td>' +
            '<td style="padding:5px 8px;min-width:90px"><div style="background:#eee;border-radius:3px;height:6px"><div style="width:' + str(bw_c) + '%;background:' + col_c + ';height:6px;border-radius:3px"></div></div>' +
            '<span style="font-size:10px;color:#aaa">' + f'{pct_c:.1f}%' + '</span></td></tr>'
        )
    coup_html = (
        '<table style="width:100%;border-collapse:collapse;font-size:12px">' +
        '<tr style="border-bottom:1.5px solid #e0e0e0">' +
        '<th style="padding:6px 8px;text-align:left;color:#555;font-size:11px">الكوبون</th>' +
        '<th style="padding:6px 8px;text-align:right;color:#555;font-size:11px">الخصم</th>' +
        '<th style="padding:6px 8px;text-align:right;color:#555;font-size:11px">أوردرات</th>' +
        '<th style="padding:6px 8px;color:#555;font-size:11px">النسبة</th></tr>' +
        coup_rows + '</table>'
    )
    st.markdown(coup_html, unsafe_allow_html=True)

# ── CUSTOMER REGION ───────────────────────────────────────────────────────────
st.markdown('<p class="section-title">مبيعات كل محافظة</p>', unsafe_allow_html=True)

region_map = {
    'Cairo':'القاهرة','Giza':'الجيزة','Alexandria':'الأسكندرية',
    'Qalyubia':'القليوبية','Al Sharqia':'الشرقية','Sohag':'سوهاج',
    'Al Monufia':'المنوفية','Al Minufiya':'المنوفية','Al Beheira':'البحيرة',
    'Al Daqahliya':'الدقهلية','Asyut':'أسيوط','Al Gharbia':'الغربية',
    'Red Sea':'البحر الأحمر','Ismailia':'الأسماعيلية','Suez':'السويس',
    'Al Fayoum':'الفيوم','Damietta':'دمياط','Qena':'قنا',
    'Port Said':'بور سعيد','Al Meniya':'المنيا','Luxor':'الأقصر',
    'Aswan':'أسوان','Bani Souaif':'بني سويف','Kafr El-Sheikh':'كفر الشيخ',
    'North Coast':'الساحل الشمالي'
}
df_reg = df[["Customer Region","Value After Discounts","Order #","Qty Ordered"]].copy()
df_reg["Region"] = df_reg["Customer Region"].map(region_map).fillna(df_reg["Customer Region"])
region_df = df_reg.groupby("Region").agg(
    revenue=("Value After Discounts","sum"),
    orders=("Order #","nunique"),
    items=("Qty Ordered","sum")
).sort_values("revenue",ascending=False).reset_index()
region_df["pct"] = (region_df["revenue"]/region_df["revenue"].sum()*100).round(1)
region_df["aov"] = (region_df["revenue"]/region_df["orders"]).round(0)

REG_PAL = ["#3266ad","#185fa5","#378add","#85b7eb","#b5d4f4","#d85a30","#ba7517","#2a9e75","#0f6e56","#533ab7","#3c3489","#993556","#639922","#854f0b","#888780"]

# Region chart — top 15 only for performance
fig_reg = go.Figure()
fig_reg.add_trace(go.Bar(
    y=region_df.head(15)["Region"], x=region_df.head(15)["revenue"],
    orientation="h",
    marker_color=[REG_PAL[min(i,len(REG_PAL)-1)] for i in range(15)],
    hovertemplate="%{y}: %{x:,.0f} ج<extra></extra>",
    text=region_df.head(15)["pct"].astype(str)+"%",
    textposition="outside"
))
fig_reg.update_layout(
    height=380, margin=dict(t=10,b=10,l=10,r=60),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(tickformat=",.0f"),
    yaxis=dict(ticks="", tickfont=dict(size=11)),
    showlegend=False
)
st.plotly_chart(fig_reg, use_container_width=True, config={"displayModeBar": False})

max_rev_reg = region_df["revenue"].max()
reg_rows = ""
for i2, (_, rr) in enumerate(region_df.iterrows(), 1):
    bw_r = int(rr["revenue"]/max_rev_reg*100) if max_rev_reg > 0 else 0
    col_r2 = REG_PAL[min(i2-1, len(REG_PAL)-1)]
    fw_r = "600" if i2 <= 3 else "400"
    reg_rows += (
        '<tr style="border-bottom:.5px solid #f0f0f0">' +
        '<td style="padding:5px 8px;color:#aaa">' + str(i2) + '</td>' +
        '<td style="padding:5px 8px;font-weight:' + fw_r + '">' + str(rr["Region"]) + '</td>' +
        '<td style="padding:5px 8px;text-align:right;font-weight:500">' + f'{rr["revenue"]:,.0f}' + '</td>' +
        '<td style="padding:5px 8px;text-align:right;color:#555">' + f'{rr["orders"]:,}' + '</td>' +
        '<td style="padding:5px 8px;text-align:right;color:#555">' + f'{rr["aov"]:,.0f}' + '</td>' +
        '<td style="padding:5px 8px;min-width:120px"><div style="background:#eee;border-radius:3px;height:6px"><div style="width:' + str(bw_r) + '%;background:' + col_r2 + ';height:6px;border-radius:3px"></div></div>' +
        '<span style="font-size:10px;font-weight:700;color:#555">' + str(rr["pct"]) + '%</span></td></tr>'
    )
reg_html = (
    '<div style="max-height:520px;overflow-y:auto">' +
    '<table style="width:100%;border-collapse:collapse;font-size:12px">' +
    '<tr style="border-bottom:1.5px solid #1F3864;position:sticky;top:0;background:#1F3864">' +
    '<th style="padding:7px 8px;text-align:left;color:white;font-size:11px">#</th>' +
    '<th style="padding:7px 8px;text-align:left;color:white;font-size:11px">المحافظة</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#b5d4f4;font-size:11px">المبيعات (ج)</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#b5d4f4;font-size:11px">الأوردرات</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#b5d4f4;font-size:11px">AOV (ج)</th>' +
    '<th style="padding:7px 8px;color:white;font-size:11px;min-width:120px">النسبة</th></tr>' +
    reg_rows + '</table></div>'
)
st.markdown(reg_html, unsafe_allow_html=True)
_reg_dl = region_df[["Region","revenue","orders","aov","pct"]].rename(columns={"Region":"المحافظة","revenue":"المبيعات (ج)","orders":"الأوردرات","aov":"AOV (ج)","pct":"النسبة %"})
st.download_button("⬇ تصدير Excel — المحافظات", to_excel(_reg_dl), "مبيعات_المحافظات.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.markdown('<p class="section-title">طرق الدفع</p>', unsafe_allow_html=True)

pay_df = df.groupby("Payment Method").agg(
    revenue=("Value After Discounts","sum"),
    orders=("Order #","nunique")
).sort_values("revenue",ascending=False).reset_index()
pay_df["pct"] = (pay_df["revenue"]/pay_df["revenue"].sum()*100).round(1)
pay_df["aov"] = (pay_df["revenue"]/pay_df["orders"]).round(0)

PAY_PAL = ["#3266ad","#d85a30","#2a9e75","#ba7517","#993556","#533ab7","#639922","#854f0b","#888780"]

col_pay1, col_pay2 = st.columns([1,1])
with col_pay1:
    fig_pay_donut = go.Figure(go.Pie(
        labels=pay_df["Payment Method"],
        values=pay_df["revenue"],
        hole=.6,
        marker_colors=PAY_PAL,
        textinfo="label+percent",
        hovertemplate="%{label}: %{value:,.0f} ج (%{percent})<extra></extra>"
    ))
    fig_pay_donut.update_layout(
        height=300, margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False
    )
    st.plotly_chart(fig_pay_donut, use_container_width=True, config={"displayModeBar": False})

with col_pay2:
    fig_pay_bar = px.bar(
        pay_df, x="Payment Method", y="revenue",
        color="Payment Method", color_discrete_sequence=PAY_PAL,
        text=pay_df["pct"].astype(str)+"%"
    )
    fig_pay_bar.update_layout(
        showlegend=False, height=300,
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="", tickfont=dict(size=9)),
        yaxis=dict(title="", tickformat=",.0f")
    )
    fig_pay_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_pay_bar, use_container_width=True, config={"displayModeBar": False})

max_rev_pay = pay_df["revenue"].max()
pay_rows = ""
for i3, (_, pr) in enumerate(pay_df.iterrows(), 1):
    bw_p = int(pr["revenue"]/max_rev_pay*100) if max_rev_pay > 0 else 0
    col_p2 = PAY_PAL[min(i3-1, len(PAY_PAL)-1)]
    fw_p = "600" if i3 == 1 else "400"
    pay_rows += (
        '<tr style="border-bottom:.5px solid #f0f0f0">' +
        '<td style="padding:5px 8px;color:#aaa">' + str(i3) + '</td>' +
        '<td style="padding:5px 8px;font-weight:' + fw_p + '">' + str(pr["Payment Method"]) + '</td>' +
        '<td style="padding:5px 8px;text-align:right;font-weight:' + fw_p + '">' + f'{pr["revenue"]:,.0f}' + '</td>' +
        '<td style="padding:5px 8px;text-align:right;color:#555">' + f'{pr["orders"]:,}' + '</td>' +
        '<td style="padding:5px 8px;text-align:right;color:#555">' + f'{pr["aov"]:,.0f}' + '</td>' +
        '<td style="padding:5px 8px;min-width:120px"><div style="background:#eee;border-radius:3px;height:6px"><div style="width:' + str(bw_p) + '%;background:' + col_p2 + ';height:6px;border-radius:3px"></div></div>' +
        '<span style="font-size:10px;font-weight:700;color:#555">' + str(pr["pct"]) + '%</span></td></tr>'
    )
pay_html = (
    '<table style="width:100%;border-collapse:collapse;font-size:12px">' +
    '<tr style="border-bottom:1.5px solid #1F3864;background:#1F3864">' +
    '<th style="padding:7px 8px;text-align:left;color:white;font-size:11px">#</th>' +
    '<th style="padding:7px 8px;text-align:left;color:white;font-size:11px">طريقة الدفع</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#b5d4f4;font-size:11px">المبيعات (ج)</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#b5d4f4;font-size:11px">الأوردرات</th>' +
    '<th style="padding:7px 8px;text-align:right;color:#b5d4f4;font-size:11px">AOV (ج)</th>' +
    '<th style="padding:7px 8px;color:white;font-size:11px;min-width:120px">النسبة</th></tr>' +
    pay_rows + '</table>'
)
st.markdown(pay_html, unsafe_allow_html=True)
_pay_dl = pay_df[["Payment Method","revenue","orders","aov","pct"]].rename(columns={"Payment Method":"طريقة الدفع","revenue":"المبيعات (ج)","orders":"الأوردرات","aov":"AOV (ج)","pct":"النسبة %"})
st.download_button("⬇ تصدير Excel — طرق الدفع", to_excel(_pay_dl), "طرق_الدفع.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
# sticky header removed for performance
st.markdown(f"<p style='text-align:center;color:#aaa;font-size:11px'>Raneen Analytics · {date_min} → {date_max}</p>", unsafe_allow_html=True)
