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

@st.cache_data(show_spinner=False, max_entries=2)
def get_price_changes(df):
    df_s = df.sort_values("Purchase Date")
    results = []
    for sku, grp in df_s.groupby("SKU"):
        grp = grp.sort_values("Purchase Date")
        prev, name, attr = None, grp.iloc[0]["Name"], grp.iloc[0]["Attribute Set"]
        changes = []
        for _, row in grp.iterrows():
            if prev is None: prev = row["Item Price"]; continue
            if row["Item Price"] != prev:
                change_date = row["Purchase Date"].strftime("%b %d")
                day_qty = grp[grp["Day"] == change_date]["Qty Ordered"].sum()
                changes.append({"SKU":sku,"Product":name,"Category":attr,
                    "Date":change_date,
                    "Price Before":prev,"Price After":row["Item Price"],
                    "Change":round(row["Item Price"]-prev,2),
                    "Qty on Day":int(day_qty)})
                prev = row["Item Price"]
        if len(changes)>=3:
            for c in changes: c["# Changes"]=len(changes)
            results.extend(changes)
    return pd.DataFrame(results) if results else pd.DataFrame()

# ── DEFAULT DATA URL ─────────────────────────────────────────────────────────
DEFAULT_DATA_URL = "https://raw.githubusercontent.com/gawadyahmed2018-web/raneen-dashboard/main/raneen_default_data.csv"
MAPPING_URL      = "https://raw.githubusercontent.com/gawadyahmed2018-web/raneen-dashboard/main/category_mapping.csv"
GSHEET_SPEND_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTvCm7gn0G_PlQTKLV-gIRkuCXbfkQ956kNrK6jmUdgqRfL5LfI6x5IhJKs6l0a0g/pub?gid=1982732416&single=true&output=csv"

# ── Monthly Targets ───────────────────────────────────────────────────────────
MONTHLY_TARGETS = {
    1:  {"budget": 6_038_416, "spend_pct": 3.60, "total": 168_716_207, "mp": 56_605_296, "retail": 112_110_911},
    2:  {"budget": 3_533_095, "spend_pct": 3.20, "total": 111_789_600, "mp": 45_003_367, "retail":  66_786_233},
    3:  {"budget": 4_214_038, "spend_pct": 3.00, "total": 140_954_260, "mp": 50_164_513, "retail":  90_789_747},
    4:  {"budget": 4_124_552, "spend_pct": 3.20, "total": 127_069_401, "mp": 54_536_761, "retail":  72_532_640},
    5:  {"budget": 4_916_567, "spend_pct": 3.30, "total": 147_585_977, "mp": 56_404_107, "retail":  91_181_870},
    6:  {"budget": 7_583_190, "spend_pct": 3.60, "total": 211_373_442, "mp": 90_894_279, "retail": 120_479_163},
    7:  {"budget": 5_966_908, "spend_pct": 3.40, "total": 174_637_356, "mp": 69_000_867, "retail": 105_636_489},
    8:  {"budget": 5_489_475, "spend_pct": 3.30, "total": 166_923_634, "mp": 63_342_181, "retail": 103_581_453},
    9:  {"budget": 4_981_784, "spend_pct": 3.40, "total": 145_805_090, "mp": 62_152_786, "retail":  83_652_304},
    10: {"budget": 4_365_925, "spend_pct": 3.10, "total": 141_978_168, "mp": 59_902_368, "retail":  82_075_800},
    11: {"budget":14_731_264, "spend_pct": 4.40, "total": 338_156_399, "mp":148_855_992, "retail": 189_300_407},
    12: {"budget": 3_871_710, "spend_pct": 3.10, "total": 125_906_478, "mp": 52_929_212, "retail":  72_977_266},
}

import calendar as _calendar

def get_period_targets(date_from, date_to):
    """
    احسب التارجت والبادجت للفترة المختارة.
    كل شهر بيتقسم بالتساوي على عدد أيامه.
    لو الفترة تغطي أكتر من شهر، بنجمع نسبة الأيام من كل شهر.
    """
    import datetime as _dt
    t_total = t_mp = t_retail = t_budget = 0.0
    current = date_from
    while current <= date_to:
        m = current.month
        days_in_month = _calendar.monthrange(current.year, m)[1]
        tgt = MONTHLY_TARGETS.get(m, {})
        daily_total  = tgt.get("total",  0) / days_in_month
        daily_mp     = tgt.get("mp",     0) / days_in_month
        daily_retail = tgt.get("retail", 0) / days_in_month
        daily_budget = tgt.get("budget", 0) / days_in_month
        t_total  += daily_total
        t_mp     += daily_mp
        t_retail += daily_retail
        t_budget += daily_budget
        current  += _dt.timedelta(days=1)
    return {"total": t_total, "mp": t_mp, "retail": t_retail, "budget": t_budget}

@st.cache_data(ttl=300, show_spinner=False, max_entries=1)
def load_default():
    import requests as _req, io as _sio, base64 as _b64
    _keep = ["Order #","Purchase Date","Day","Marketplace Seller","Seller_Raw",
             "Attribute Set","Name","SKU","Qty Ordered","Item Price","Row Total",
             "Discount Amount","Value After Discounts","Coupon Code","Customer Region","Payment Method"]
    # أولاً: GitHub API
    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
        if token:
            api_url = "https://api.github.com/repos/gawadyahmed2018-web/raneen-dashboard/contents/raneen_default_data.csv"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            r = _req.get(api_url, headers=headers, timeout=15)
            if r.status_code == 200:
                csv_bytes = _b64.b64decode(r.json()["content"].replace("\n",""))
                df = pd.read_csv(_sio.BytesIO(csv_bytes), usecols=lambda c: c in _keep)
                if not df.empty:
                    for _c in df.select_dtypes("float64").columns:
                        df[_c] = df[_c].astype("float32")
                    for _c in ["Attribute Set","Marketplace Seller","Customer Region","Payment Method"]:
                        if _c in df.columns: df[_c] = df[_c].astype("category")
                    return df
    except Exception:
        pass
    # ثانياً: raw URL
    try:
        r = _req.get(DEFAULT_DATA_URL, timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(_sio.StringIO(r.text), usecols=lambda c: c in _keep)
            if not df.empty:
                for _c in df.select_dtypes("float64").columns:
                    df[_c] = df[_c].astype("float32")
                for _c in ["Attribute Set","Marketplace Seller","Customer Region","Payment Method"]:
                    if _c in df.columns: df[_c] = df[_c].astype("category")
                return df
    except Exception:
        pass
    return None

@st.cache_data(ttl=600, show_spinner=False)
def load_spend():
    """
    جيب عمودي التاريخ (col B = index 1) والانفاق (col M = index 12).
    الشيت: صف 0 عنوان، صف 1 فئات، صف 2 أسماء أعمدة، صفوف شهرية header.
    التاريخ بصيغة "01-Jan"، الأرقام بفواصل "290,139".
    """
    try:
        import io as _io
        df_raw = pd.read_csv(GSHEET_SPEND_URL, header=None)
        rows = []
        for _, row in df_raw.iterrows():
            date_val  = str(row.iloc[1]).strip()
            spend_val = str(row.iloc[12]).strip()
            # تجاهل الصفوف الفاضية أو الـ headers
            if not date_val or date_val in ["nan", "Date", "Day"] or "Jan" not in date_val and "Feb" not in date_val and "Mar" not in date_val and "Apr" not in date_val and "May" not in date_val and "Jun" not in date_val and "Jul" not in date_val and "Aug" not in date_val and "Sep" not in date_val and "Oct" not in date_val and "Nov" not in date_val and "Dec" not in date_val:
                continue
            # تنظيف الأرقام
            spend_clean = spend_val.replace(",","").replace("%","").strip()
            if not spend_clean or spend_clean in ["nan","Total Spend","Total_Spend","-"]:
                continue
            try:
                # نجرب بدون سنة أولاً (pandas بيحدد السنة أوتوماتيك)
                dt = pd.to_datetime(date_val, format="%d-%b", errors="raise")
                # نضيف السنة الصح بناءً على الشهر
                import datetime as _dt2
                cur_year = _dt2.date.today().year
                dt = dt.replace(year=cur_year)
                spend = float(spend_clean)
                if spend > 0:
                    rows.append({"Date": dt, "Total_Spend": spend})
            except Exception:
                try:
                    # fallback: جرب مع السنة المكتوبة في الشيت
                    dt = pd.to_datetime(date_val, dayfirst=True, errors="raise")
                    spend = float(spend_clean)
                    if spend > 0:
                        rows.append({"Date": dt, "Total_Spend": spend})
                except Exception:
                    continue
        df_spend = pd.DataFrame(rows)
        if df_spend.empty:
            return df_spend
        df_spend["Day"] = df_spend["Date"].dt.strftime("%b %d")
        return df_spend
    except Exception:
        return pd.DataFrame(columns=["Date","Total_Spend","Day"])

@st.cache_data(ttl=86400, max_entries=1, show_spinner=False)
def load_mapping():
    try:
        df_m = pd.read_csv(MAPPING_URL)
        return df_m.set_index("attribute_set_name")["first_category"].to_dict()
    except Exception:
        # Fallback: hardcoded from category_mapping.xlsx
        return {
            'Yogurt Maker':'Appliances','Water Heaters':'Appliances','Water Dispenser':'Appliances',
            'Washers & Dryer':'Appliances','Vacuum Cleaners':'Appliances','Toasters':'Appliances',
            'Tanks':'Appliances','Suction Fan':'Appliances','Sandwich Waffle Makers':'Appliances',
            'Refrigerators & Freezers':'Appliances','Pressure Cooker':'Appliances',
            'Mixers & Blenders':'Appliances','Microwaves & Ovens':'Appliances',
            'Kitchen Machine & Kneading Machines':'Appliances','Kettles':'Appliances',
            'Juicers':'Appliances','Irons':'Appliances','Insect Killer':'Appliances',
            'Heaters':'Appliances','Grinders':'Appliances','Grill':'Appliances',
            'Fryers':'Appliances','Fans':'Appliances','Electric Slicers':'Appliances',
            'Electric Meat Grinders':'Appliances','Dishwasher':'Appliances',
            'Cookware':'Appliances','Cookers':'Appliances','Coffee Makers':'Appliances',
            'Burner':'Appliances','Built in':'Appliances','Baking Tools':'Appliances',
            'Air Conditioner':'Appliances','Air Coolers':'Appliances',
            'Televisions':'Electronics','Smart Watches':'Electronics',
            'Security & Surveillance Systems':'Electronics','Scanners':'Electronics',
            'Remote Units':'Electronics','Printers':'Electronics','Power Banks':'Electronics',
            'Monitors':'Electronics','Mobile Cable':'Electronics','Laptop Accessories':'Electronics',
            'Electronics Storage & Accessories':'Electronics','Electronics Audio':'Electronics',
            'Chargers':'Electronics','Car Audio':'Electronics','Car Amplifiers':'Electronics',
            'Cameras':'Electronics','AirPods':'Electronics',
            'Mobile Phones':'Mobiles','Mobile Accessories':'Mobiles',
            'Wardrobe':'Furniture','TV Table':'Furniture','TV Stand & Accessories':'Furniture',
            'Textile':'Furniture','Storage Units':'Furniture','Storage':'Furniture',
            'Sofa':'Furniture','Side Table':'Furniture','Shoe Rack':'Furniture',
            'Shelves':'Furniture','Safes and Safe Accessories':'Furniture',
            'Nursery Furniture & Decor':'Furniture','Living Rooms':'Furniture',
            'Garden Swing':'Furniture','Garden Furniture':'Furniture','Desks':'Furniture',
            'Dressing Table':'Furniture','Commode & Drawer Units':'Furniture',
            'Clothes Hangers':'Furniture','Chairs':'Furniture','Center Table':'Furniture',
            'Beds':'Furniture','Bean Bags':'Furniture','Office Chairs':'Furniture',
            'Kitchen Rooms':'Furniture',
            'Water Filters':'Home','Water Filters Accessories':'Home',
            'Wall Decor':'Home','Table Lighting':'Home','Picture Frames':'Home',
            'Mirror':'Home','Lighting Hanging':'Home','Home Decor':'Home',
            'Floor Lamp':'Home','Curtain':'Home','Carpets':'Home',
            'Bathroom Accessories':'Home','Home & Balcony Essentials':'Home',
            'Serveware':'Kitchen','Kitchenware':'Kitchen','Kitchen Scale':'Kitchen',
            'Kitchen Accessories':'Kitchen','Drinkware':'Kitchen','Baking Tools':'Kitchen',
            'Towels':'Textile','Pillows':'Textile','Mattress':'Textile',
            'Bed Sheets':'Textile','Bedding':'Textile',
            'Tops and T-shirts':'Fashion','Underwears':'Fashion','Sportswear':'Fashion',
            'Shoes':'Fashion','Perfumes':'Fashion','Pajamas & Sleepwear':'Fashion',
            'Mens Bags':'Fashion','Makeup':'Fashion','Luggage':'Fashion',
            'Hair Care':'Fashion','Hair Treatments':'Fashion',
            'Beauty & Body Care':'Fashion','Watches':'Fashion','Watches & Alarms':'Fashion',
            'Sports Equipment':'Family Products','Soap & Shower Gel':'Family Products',
            'Skin Care':'Family Products','Shaving & Grooming':'Family Products',
            'Shampoos & Conditioners':'Family Products','Sewing Machines':'Family Products',
            'Scooters':'Family Products','Pet Supplies':'Family Products',
            'Pet Foods':'Family Products','PlayStation & Accessories':'Family Products',
            'PlayStation Games & Accessories':'Family Products',
            'Nursery Furniture & Decor':'Family Products','Dolls':'Family Products',
            'Diapers':'Family Products','Child Safety':'Family Products',
            'Car Video':'Family Products','Car Tires':'Family Products',
            'Car Speakers':'Family Products','Car Parts And Services':'Family Products',
            'Car Care':'Family Products','Car Audio':'Family Products',
            'Bike & Scooters':'Family Products','Baby Feeding':'Family Products',
            'Baby Care':'Family Products','Baby Accessories':'Family Products',
            'Activities & Books':'Family Products','Action Toys':'Family Products',
            'Baby Gears':'Family Products','Dolls':'Family Products',
        }

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Raneen Analytics")
    st.markdown("---")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#d85a30,#e87a50);border-radius:10px;padding:1rem 1rem;text-align:center;margin-bottom:.75rem;box-shadow:0 3px 10px rgba(216,90,48,.35)">
      <p style="color:white;font-size:15px;font-weight:800;margin:0 0 4px;letter-spacing:.02em">⬆️ أضف الشيت المحدَّث هنا</p>
      <p style="color:rgba(255,255,255,.85);font-size:11px;margin:0">CSV من ماجينتو ← الداشبورد يتحدث فوراً</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>
    [data-testid="stFileUploader"] {
        border: 2px dashed #d85a30 !important;
        border-radius: 8px !important;
        background: rgba(216,90,48,.06) !important;
    }
    [data-testid="stFileUploader"] label { color: #d85a30 !important; font-weight: 600 !important; }
    [data-testid="stFileUploaderDropzone"] { background: transparent !important; }
    [data-testid="stFileUploaderDropzoneInstructions"] svg { fill: #d85a30 !important; }
    [data-testid="stFileUploaderDropzoneInstructions"] span { color: #d85a30 !important; font-weight:600 !important; }
    </style>
    """, unsafe_allow_html=True)
    uploaded = st.file_uploader("", type=["csv"], label_visibility="collapsed")

    # Auto-save processed CSV to GitHub when file uploaded
    if uploaded is not None:
        import base64, requests, io as _io
        try:
            token = st.secrets["GITHUB_TOKEN"]
            repo  = "gawadyahmed2018-web/raneen-dashboard"
            gh_headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

            # Process uploaded file
            uploaded.seek(0)
            df_processed = process(uploaded)

            def _upload_to_github(path, df_to_save, label):
                buf = _io.StringIO()
                df_to_save.to_csv(buf, index=False)
                raw = buf.getvalue().encode("utf-8")
                # تأكد إن الداتا مش فاضية قبل الرفع
                if len(raw) < 100:
                    return False
                encoded = base64.b64encode(raw).decode()
                api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
                r_get = requests.get(api_url, headers=gh_headers)
                sha = r_get.json().get("sha", "") if r_get.status_code == 200 else ""
                payload = {"message": f"Auto-update {label}", "content": encoded, "sha": sha}
                r_put = requests.put(api_url, headers=gh_headers, json=payload)
                return r_put.status_code in [200, 201]

            # 1. Save as latest default
            ok_default = _upload_to_github("raneen_default_data.csv", df_processed, "default data")

            # 2. Save monthly archive automatically
            df_processed["_dt"] = pd.to_datetime(df_processed["Purchase Date"], errors="coerce")
            df_processed["_ym"] = df_processed["_dt"].dt.to_period("M").astype(str)
            monthly_saved = []
            for ym in df_processed["_ym"].dropna().unique():
                df_month = df_processed[df_processed["_ym"] == ym].drop(columns=["_dt","_ym"], errors="ignore")
                fname = "archive/raneen_" + ym.replace("-", "_") + ".csv"
                if _upload_to_github(fname, df_month, ym):
                    monthly_saved.append(ym)
            df_processed.drop(columns=["_dt","_ym"], errors="ignore", inplace=True)

            if ok_default:
                st.cache_data.clear()  # امسح كل الكاش عشان يجيب الداتا الجديدة
                msg = "✅ اتحفظ كـ Default أوتوماتيك!"
                if monthly_saved:
                    msg += f"  |  📁 أرشيف: {', '.join(monthly_saved)}"
                st.success(msg)
            else:
                st.warning("⚠️ الداشبورد شغال بس التحديث التلقائي فشل")
            uploaded.seek(0)
        except Exception:
            uploaded.seek(0)

    st.markdown("---")
    _archive_months = {
        "الشهر الحالي (Default)": None,
        "يونيو 2026":   "archive/raneen_2026_06.csv",
        "مايو 2026":    "archive/raneen_2026_05.csv",
        "أبريل 2026":   "archive/raneen_2026_04.csv",
        "مارس 2026":    "archive/raneen_2026_03.csv",
    }
    _sel_archive = st.selectbox("اختار شهر", list(_archive_months.keys()), label_visibility="collapsed")
    
    # مقارنة شهرين — merge يونيو مع يوليو اختياري
    _merge_prev = st.checkbox("📅 ضم الشهر السابق", value=False, 
        help="يدمج الشهر السابق مع الحالي — ممكن يبطئ الأداء")
    st.markdown("---")
    st.markdown("**كيفية الاستخدام:**")
    st.markdown("1. نزّل الشيت من ماجينتو\n2. ارفعه هنا\n3. الداشبورد بيظهر فوراً")

# ── MAIN ─────────────────────────────────────────────────────────────────────
using_default = uploaded is None

if using_default:
    # Check if user selected an archive month
    _archive_path = _archive_months.get(_sel_archive)
    if _archive_path:
        @st.cache_data(ttl=3600, show_spinner=False)
        def load_archive(path):
            import requests as _req, io as _sio, base64 as _b64
            try:
                token = st.secrets.get("GITHUB_TOKEN", "")
                api_url = f"https://api.github.com/repos/gawadyahmed2018-web/raneen-dashboard/contents/{path}"
                headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                r = _req.get(api_url, headers=headers, timeout=15)
                if r.status_code == 200:
                    csv_bytes = _b64.b64decode(r.json()["content"].replace("\n",""))
                    return pd.read_csv(_sio.BytesIO(csv_bytes))
            except Exception:
                pass
            return None
        df_full = load_archive(_archive_path)
        if df_full is None:
            st.warning(f"⚠️ مش لاقي الأرشيف — تأكد إن الملف موجود على GitHub.")
            st.stop()
        st.sidebar.success(f"📁 عارض: {_sel_archive}")
    else:
        df_full = load_default()
        if df_full is None:
            st.warning("⚠️ لا توجد بيانات محفوظة — ارفع شيت ماجينتو من القايمة الجانبية لتشغيل الداشبورد.")
            st.info("💡 بعد الرفع، الداشبورد بيتحدث أوتوماتيك ويحفظ الداتا للمرات الجاية.")
            st.stop()
    df_full["Purchase Date"] = pd.to_datetime(df_full["Purchase Date"], errors="coerce")
    if "Day" not in df_full.columns:
        df_full["Day"] = df_full["Purchase Date"].dt.strftime("%b %d")

    # ── ضم الشهر السابق — اختياري ──
    if _merge_prev and _sel_archive == "الشهر الحالي (Default)":
        import requests as _req3, io as _sio3
        try:
            _cur_m = int(df_full["Purchase Date"].dt.month.mode()[0])
            _cur_y = int(df_full["Purchase Date"].dt.year.mode()[0])
            _prev_m = _cur_m - 1
            if _prev_m > 0:
                _prev_url = f"https://raw.githubusercontent.com/gawadyahmed2018-web/raneen-dashboard/main/archive/raneen_{_cur_y}_{str(_prev_m).zfill(2)}.csv"
                _tok = st.secrets.get("GITHUB_TOKEN", "")
                _rp = _req3.get(_prev_url, headers={"Authorization": f"token {_tok}"}, timeout=15)
                if _rp.status_code == 200:
                    _df_prev = pd.read_csv(_sio3.StringIO(_rp.text))
                    _df_prev["Purchase Date"] = pd.to_datetime(_df_prev["Purchase Date"], errors="coerce")
                    if "Day" not in _df_prev.columns:
                        _df_prev["Day"] = _df_prev["Purchase Date"].dt.strftime("%b %d")
                    for _mc2 in _df_prev.select_dtypes("float64").columns:
                        _df_prev[_mc2] = _df_prev[_mc2].astype("float32")
                    df_full = pd.concat([_df_prev, df_full], ignore_index=True)
                    df_full = df_full.sort_values("Purchase Date").reset_index(drop=True)
                    del _df_prev
                    import gc; gc.collect()
                    st.sidebar.success(f"✅ تم دمج الشهر السابق")
        except Exception:
            pass
else:
    df_full = process(uploaded)
all_days = sorted(df_full["Day"].unique(), key=lambda d: pd.to_datetime(d+" 2026"))
all_dates = sorted(df_full["Purchase Date"].dt.date.unique())

# ── DATE RANGE FILTER ────────────────────────────────────────────────────────
# ── STICKY HEADER ────────────────────────────────────────────────────────────
st.markdown("""
<style>
.sticky-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999;
    background: #1F3864;
    padding: .55rem 2rem .55rem 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18);
}
.sticky-header .title {
    font-size: 18px;
    font-weight: 800;
    color: white;
    margin: 0;
    letter-spacing: .02em;
}
.sticky-header .sub {
    font-size: 11px;
    color: #85b7eb;
    margin: 2px 0 0;
}
.sticky-header .date-badge {
    background: rgba(255,255,255,.12);
    border-radius: 8px;
    padding: 5px 14px;
    text-align: center;
}
.sticky-header .date-badge .d1 {
    font-size: 11px;
    color: #b5d4f4;
    margin: 0;
}
.sticky-header .date-badge .d2 {
    font-size: 13px;
    font-weight: 700;
    color: white;
    margin: 0;
}
/* push page content below sticky header */
[data-testid="stAppViewContainer"] > section > div:first-child {
    padding-top: 64px !important;
}
</style>
""", unsafe_allow_html=True)

_hcol1, _hcol2 = st.columns([5, 1])
with _hcol1:
    st.markdown("# 📊 Raneen Sales Dashboard")
    st.markdown('<p style="background:linear-gradient(90deg,#1F3864,#3266ad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:19px;font-weight:800;margin-top:-8px;letter-spacing:.02em">✦ Created by Ahmed Khamis</p>', unsafe_allow_html=True)
with _hcol2:
    try:
        from PIL import Image
        _logo = Image.open("/mnt/user-data/outputs/raneen_logo.jpg")
        st.image(_logo, width=110)
    except Exception:
        pass
st.markdown("---")

# ── CHANNEL FILTER ────────────────────────────────────────────────────────────
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] > div:has(> div[data-testid="stButtonGroup"]) button {
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 8px 24px !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

_ch_col1, _ch_col2 = st.columns([3, 2])
with _ch_col1:
    _channel_filter = st.radio(
        "فلتر بالقناة",
        ["📊 الكل", "🏪 Retail (Raneen)", "🏬 Marketplace (MP)"],
        horizontal=True,
        key="channel_filter",
        label_visibility="collapsed"
    )

col_dr1, col_dr2, col_dr3 = st.columns([2,2,3])
with col_dr1:
    date_from = st.date_input("من يوم", value=all_dates[0], min_value=all_dates[0], max_value=all_dates[-1], key="date_from")
with col_dr2:
    date_to = st.date_input("إلى يوم", value=all_dates[-1], min_value=all_dates[0], max_value=all_dates[-1], key="date_to")
with col_dr3:
    st.markdown("")
    st.markdown("")
    n_days_selected = (date_to - date_from).days + 1
    st.info(f"📅 **{date_from.strftime('%b %d')}  →  {date_to.strftime('%b %d')}**  ·  {n_days_selected} يوم")

st.markdown("---")

days_range = [d for d in all_days if date_from <= pd.to_datetime(d+" 2026").date() <= date_to]
df = df_full[df_full["Day"].isin(days_range)].copy()

# Apply channel filter
if _channel_filter == "🏪 Retail (Raneen)":
    df = df[df["Marketplace Seller"] == "raneen"].copy()
elif _channel_filter == "🏬 Marketplace (MP)":
    df = df[df["Marketplace Seller"] == "MP"].copy()

# Apply category mapping
_cat_map = load_mapping()
df["Main Category"] = df["Attribute Set"].str.replace("&amp;","&").map(_cat_map).fillna("Other")

# Load spend data from Google Sheet and filter by selected date range
try:
    df_spend = load_spend()
except Exception:
    df_spend = pd.DataFrame(columns=["Date","Total_Spend","Day"])
df_spend_filtered = df_spend[
    (df_spend["Date"].dt.date >= date_from) &
    (df_spend["Date"].dt.date <= date_to)
] if not df_spend.empty else pd.DataFrame(columns=["Date","Total_Spend","Day"])

total_spend    = df_spend_filtered["Total_Spend"].sum()
spend_per_day  = df_spend_filtered.groupby("Day")["Total_Spend"].sum()

date_min = df["Purchase Date"].dt.date.min()
date_max = df["Purchase Date"].dt.date.max()

total   = df["Value After Discounts"].sum()
df_r    = df[df["Marketplace Seller"]=="raneen"]
df_mp   = df[df["Marketplace Seller"]=="MP"]
raneen  = df_r["Value After Discounts"].sum()
mp      = df_mp["Value After Discounts"].sum()

total_orders  = df["Order #"].nunique()
raneen_orders = df_r["Order #"].nunique()
mp_orders     = df_mp["Order #"].nunique()

total_qty  = df["Qty Ordered"].sum()
raneen_qty = df_r["Qty Ordered"].sum()
mp_qty     = df_mp["Qty Ordered"].sum()

aov_total  = total  / total_orders  if total_orders  else 0
aov_raneen = raneen / raneen_orders if raneen_orders else 0
aov_mp     = mp     / mp_orders     if mp_orders     else 0

days_sorted = days_range

# ── Calculate period targets ──────────────────────────────────────────────────
_period_tgt = get_period_targets(date_from, date_to)
_tgt_total   = _period_tgt["total"]
_tgt_mp      = _period_tgt["mp"]
_tgt_retail  = _period_tgt["retail"]
_tgt_budget  = _period_tgt["budget"]

# Achievement percentages
_ach_total   = total  / _tgt_total  * 100 if _tgt_total  > 0 else 0
_ach_raneen  = raneen / _tgt_retail * 100 if _tgt_retail > 0 else 0
_ach_mp      = mp     / _tgt_mp     * 100 if _tgt_mp     > 0 else 0

def _ach_color(pct):
    if pct >= 100: return "#2a9e75"
    if pct >= 80:  return "#ba7517"
    return "#d85a30"

def _make_gauge(pct, label, value_str, target_str, color):
    """Lightweight HTML progress bar instead of heavy plotly gauge."""
    bar_color = _ach_color(pct)
    bar_w = min(pct, 100)
    icon = "✅" if pct >= 100 else "🔶" if pct >= 80 else "🔴"
    return (
        f'<div style="background:var(--color-background-secondary);border-radius:10px;padding:.8rem 1rem;margin-bottom:4px">' +
        f'<p style="font-size:11px;color:#888;margin:0 0 4px">{label}</p>' +
        f'<p style="font-size:18px;font-weight:600;color:{bar_color};margin:0">{value_str}</p>' +
        f'<p style="font-size:10px;color:#aaa;margin:2px 0 6px">تارجت: {target_str}</p>' +
        f'<div style="background:#e0e0e0;border-radius:4px;height:8px">' +
        f'<div style="width:{bar_w:.0f}%;background:{bar_color};height:8px;border-radius:4px;transition:width .3s"></div></div>' +
        f'<p style="font-size:12px;font-weight:700;color:{bar_color};margin:4px 0 0">{icon} {pct:.1f}%</p>' +
        f'</div>'
    )


# ── METRICS ROW 1: Sales ──────────────────────────────────────────────────────
st.markdown('<p class="section-title">المبيعات الإجمالية</p>', unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
# ── Achievement bars (lightweight) ──────────────────────────────────────────
g1, g2, g3 = st.columns(3)
with g1:
    st.markdown(_make_gauge(_ach_total, "إجمالي المبيعات", f"{total/1e6:.2f}M ج", f"{_tgt_total/1e6:.2f}M ج", "#1F3864"), unsafe_allow_html=True)
with g2:
    st.markdown(_make_gauge(_ach_raneen, "Raneen", f"{raneen/1e6:.2f}M ج", f"{_tgt_retail/1e6:.2f}M ج", "#3266ad"), unsafe_allow_html=True)
with g3:
    st.markdown(_make_gauge(_ach_mp, "MP", f"{mp/1e6:.2f}M ج", f"{_tgt_mp/1e6:.2f}M ج", "#d85a30"), unsafe_allow_html=True)

# ── Metric cards row (numbers detail) ────────────────────────────────────────
with c1:
    st.markdown(f'<div class="metric-card"><p class="metric-label">إجمالي المبيعات</p><p class="metric-value">{total/1e6:.2f}M ج</p><p class="metric-sub">{total_orders:,} أوردر · تحقيق: <b style="color:{_ach_color(_ach_total)}">{_ach_total:.1f}%</b></p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card" style="border-left:4px solid #3266ad"><p class="metric-label">مبيعات Raneen</p><p class="metric-value" style="color:#3266ad">{raneen/1e6:.2f}M ج</p><p class="metric-sub">{raneen_orders:,} أوردر · تحقيق: <b style="color:{_ach_color(_ach_raneen)}">{_ach_raneen:.1f}%</b></p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card" style="border-left:4px solid #d85a30"><p class="metric-label">مبيعات MP</p><p class="metric-value" style="color:#d85a30">{mp/1e6:.2f}M ج</p><p class="metric-sub">{mp_orders:,} أوردر · تحقيق: <b style="color:{_ach_color(_ach_mp)}">{_ach_mp:.1f}%</b></p></div>', unsafe_allow_html=True)

# ── METRICS ROW 2: AOV ────────────────────────────────────────────────────────
c4,c5,c6 = st.columns(3)
with c4:
    st.markdown(f'<div class="metric-card"><p class="metric-label">AOV الإجمالي</p><p class="metric-value">{aov_total:,.0f} ج</p><p class="metric-sub">متوسط قيمة الأوردر</p></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="metric-card" style="border-left:4px solid #3266ad"><p class="metric-label">AOV — Raneen</p><p class="metric-value" style="color:#3266ad">{aov_raneen:,.0f} ج</p></div>', unsafe_allow_html=True)
with c6:
    st.markdown(f'<div class="metric-card" style="border-left:4px solid #d85a30"><p class="metric-label">AOV — MP</p><p class="metric-value" style="color:#d85a30">{aov_mp:,.0f} ج</p></div>', unsafe_allow_html=True)

# ── METRICS ROW 3: Qty ────────────────────────────────────────────────────────
c7,c8,c9 = st.columns(3)
with c7:
    st.markdown(f'<div class="metric-card"><p class="metric-label">إجمالي القطع المباعة</p><p class="metric-value">{total_qty:,}</p><p class="metric-sub">Qty Ordered</p></div>', unsafe_allow_html=True)
with c8:
    st.markdown(f'<div class="metric-card" style="border-left:4px solid #3266ad"><p class="metric-label">قطع Raneen</p><p class="metric-value" style="color:#3266ad">{raneen_qty:,}</p><p class="metric-sub">{raneen_qty/total_qty*100:.1f}% من الإجمالي</p></div>', unsafe_allow_html=True)
with c9:
    st.markdown(f'<div class="metric-card" style="border-left:4px solid #d85a30"><p class="metric-label">قطع MP</p><p class="metric-value" style="color:#d85a30">{mp_qty:,}</p><p class="metric-sub">{mp_qty/total_qty*100:.1f}% من الإجمالي</p></div>', unsafe_allow_html=True)

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

# ── PRICE CHANGES with category dropdown ──────────────────────────────────────
st.markdown('<p class="section-title">المنتجات التي تغير سعرها أكثر من 3 مرات</p>', unsafe_allow_html=True)

# Apply main category filter to price changes
_df_for_pc = df.copy()
if _sel_main_cat != "كل الأقسام":
    _df_for_pc = _df_for_pc[_df_for_pc["Main Category"] == _sel_main_cat]

pc = get_price_changes(_df_for_pc)
if not pc.empty:
    pc["Category"] = pc["Category"].str.replace("&amp;","&")
    cats_available = ["الكل"] + sorted(pc["Category"].unique().tolist())
    selected_cat = st.selectbox("فلتر بالقسم", cats_available, key="pc_cat")
    pc_show = pc if selected_cat=="الكل" else pc[pc["Category"]==selected_cat]
    pc_show = pc_show.sort_values(["# Changes","SKU"], ascending=[False,True])

    top15_skus = pc_show.drop_duplicates("SKU")["SKU"].head(10).tolist()
    pc_show = pc_show[pc_show["SKU"].isin(top15_skus)]

    n_prods = pc_show["SKU"].nunique()
    _pc_col1, _pc_col2 = st.columns([3,1])
    with _pc_col1:
        st.caption(f"عرض أعلى {n_prods} منتج (الأكثر تغييراً) · {len(pc_show)} تغيير")
    with _pc_col2:
        st.download_button("⬇ تصدير Excel", to_excel(pc_show), "تغييرات_السعر.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    pc_show = pc_show.copy()
    pc_html = """<div style='max-height:480px;overflow-y:auto'><table style='width:100%;border-collapse:collapse;font-size:12px'>
<tr style='border-bottom:1.5px solid #1F3864;position:sticky;top:0;background:#1F3864;z-index:2'>
<th style='padding:7px 10px;text-align:left;color:white;font-size:11px;width:30%'>المنتج</th>
<th style='padding:7px 10px;text-align:left;color:white;font-size:11px;width:12%'>التاريخ</th>
<th style='padding:7px 10px;text-align:right;color:#b5d4f4;font-size:11px'>قبل (ج)</th>
<th style='padding:7px 10px;text-align:right;color:#b5d4f4;font-size:11px'>بعد (ج)</th>
<th style='padding:7px 10px;text-align:right;color:white;font-size:11px'>الفرق</th>
<th style='padding:7px 10px;text-align:right;color:#9fe1cb;font-size:11px'>كمية اليوم</th>
<th style='padding:7px 10px;text-align:center;color:white;font-size:11px'># تغييرات</th>
</tr>"""
    last_sku = None
    for _, row in pc_show.iterrows():
        is_new = row["SKU"] != last_sku
        if is_new:
            last_sku = row["SKU"]
            n = int(row["# Changes"])
            nbg = "#faeeda" if n>=7 else "#e1f5ee" if n>=6 else "#e6f1fb" if n>=5 else "#fcebeb" if n>=4 else "#f5f5f5"
            nc  = "#633806" if n>=7 else "#085041" if n>=6 else "#0c447c" if n>=5 else "#501313" if n>=4 else "#555"
            name_short = str(row["Product"])[:55] + ("..." if len(str(row["Product"]))>55 else "")
            pc_html += f"""<tr style='border-top:2px solid #d0d0d0;background:#fafafa'>
<td colspan='6' style='padding:7px 10px;font-weight:600;font-size:12px;color:#1F3864'>{name_short}<br>
<span style='font-family:monospace;font-size:10px;color:#888'>{row["SKU"]}</span>
<span style='font-size:10px;color:#888;margin-right:6px'>· {row["Category"]}</span></td>
<td style='padding:7px 10px;text-align:center'><span style='background:{nbg};color:{nc};padding:2px 7px;border-radius:8px;font-size:11px;font-weight:600'>{n}x</span></td>
</tr>"""
        change_val = row["Change"]
        chg_color = "#2a9e75" if change_val > 0 else "#d85a30"
        chg_str   = f'+{change_val:,.0f}' if change_val > 0 else f'{change_val:,.0f}'
        qty_day   = int(row.get("Qty on Day", 0))
        pc_html += f"""<tr style='border-bottom:.5px solid #eee'>
<td style='padding:5px 10px;color:#aaa;font-size:11px'>↳</td>
<td style='padding:5px 10px;color:#555'>{row["Date"]}</td>
<td style='padding:5px 10px;text-align:right;color:#555'>{row["Price Before"]:,.0f}</td>
<td style='padding:5px 10px;text-align:right;font-weight:500'>{row["Price After"]:,.0f}</td>
<td style='padding:5px 10px;text-align:right;font-weight:600;color:{chg_color}'>{chg_str}</td>
<td style='padding:5px 10px;text-align:right;font-weight:600;color:#533ab7'>{qty_day:,}</td>
<td></td>
</tr>"""
    pc_html += "</table></div>"
    st.markdown(pc_html, unsafe_allow_html=True)
else:
    st.info("لا توجد منتجات بأكثر من 3 تغييرات في السعر")
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
