"""
Raneen Analytics Hub — Landing Page.
Full brand-red background with big RANEEN logo, glassy clickable page cards,
and author credit. Entry point of the multi-page app.
"""

import streamlit as st

st.set_page_config(page_title="Raneen Analytics Hub", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

R = {
    "red": "#E11D2A", "red2": "#C2101C", "red_dark": "#8A0B14",
    "ink": "#1A1A2E", "ink2": "#5B6472", "ink3": "#94A0B0",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family:'Inter','IBM Plex Sans Arabic',sans-serif; }}
#MainMenu, footer {{ visibility:hidden; }}
[data-testid="stHeader"] {{ background:rgba(0,0,0,0); }}

/* Full brand-red background across the whole app */
.stApp {{
  background: linear-gradient(160deg, {R['red']} 0%, {R['red2']} 45%, {R['red_dark']} 100%);
  background-attachment: fixed;
}}
.block-container {{ padding:0 2.4rem 3rem; max-width:1320px; }}

/* soft light orbs */
.stApp::before {{
  content:''; position:fixed; top:-8%; right:-6%; width:620px; height:620px;
  background:radial-gradient(circle, rgba(255,255,255,.13) 0%, transparent 70%); pointer-events:none;
}}
.stApp::after {{
  content:''; position:fixed; bottom:-12%; left:-8%; width:560px; height:560px;
  background:radial-gradient(circle, rgba(255,255,255,.09) 0%, transparent 70%); pointer-events:none;
}}

/* ── HERO ── */
.hero {{ text-align:center; padding:66px 20px 8px; position:relative; }}
.logo {{
  font-size:96px; font-weight:900; color:#fff; letter-spacing:-.04em; line-height:1;
  margin-bottom:14px; text-shadow:0 6px 30px rgba(0,0,0,.22);
}}
.logo .dot {{ color:#FFD5D8; }}
.hero-sub {{ font-size:34px; font-weight:800; color:#fff; letter-spacing:.01em; text-shadow:0 2px 14px rgba(0,0,0,.14); }}
.hero-tag {{ font-size:15px; color:rgba(255,255,255,.82); margin-top:14px; }}
.hero-badge {{
  display:inline-flex; align-items:center; gap:7px; background:rgba(255,255,255,.15);
  border:1px solid rgba(255,255,255,.28); border-radius:100px; padding:7px 18px;
  font-size:12.5px; font-weight:600; color:#fff; margin-top:22px; backdrop-filter:blur(8px);
}}

.grid-title {{ font-size:16px; font-weight:700; color:#fff; text-align:center; margin:50px 0 4px; }}
.grid-sub {{ font-size:13px; color:rgba(255,255,255,.72); text-align:center; margin-bottom:28px; }}

/* ── glassy page cards ── */
.pcard {{
  background:rgba(255,255,255,.13); border:1px solid rgba(255,255,255,.22); border-radius:22px;
  padding:26px 24px; backdrop-filter:blur(14px); transition:all .2s ease; height:100%;
  box-shadow:0 8px 30px rgba(0,0,0,.10);
}}
.pcard:hover {{ transform:translateY(-5px); background:rgba(255,255,255,.2); box-shadow:0 18px 40px rgba(0,0,0,.18); }}
.pcard-ico {{ width:56px; height:56px; border-radius:16px; background:rgba(255,255,255,.9); display:flex; align-items:center; justify-content:center; font-size:27px; margin-bottom:16px; box-shadow:0 4px 12px rgba(0,0,0,.12); }}
.pcard-t {{ font-size:18px; font-weight:750; color:#fff; margin-bottom:6px; }}
.pcard-d {{ font-size:12.5px; color:rgba(255,255,255,.8); line-height:1.6; margin-bottom:16px; min-height:52px; }}

/* real page_link styled as a white button on red */
[data-testid="stPageLink"] {{ margin-top:-4px; }}
[data-testid="stPageLink"] a {{
  background:#fff; border-radius:12px; padding:11px 16px; justify-content:center; border:none;
  transition:all .2s; box-shadow:0 4px 12px rgba(0,0,0,.12);
}}
[data-testid="stPageLink"] a:hover {{ background:#FFF0F1; transform:translateY(-1px); }}
[data-testid="stPageLink"] a p {{ color:{R['red']} !important; font-weight:800 !important; font-size:13.5px !important; }}

/* author credit */
.credit {{
  text-align:center; margin:52px auto 0; padding:20px 30px; max-width:420px;
  background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.22);
  border-radius:20px; backdrop-filter:blur(10px);
}}
.credit-by {{ font-size:11px; color:rgba(255,255,255,.7); font-weight:600; letter-spacing:.08em; text-transform:uppercase; }}
.credit-name {{ font-size:20px; color:#fff; font-weight:800; margin-top:4px; letter-spacing:.01em; }}
.credit-role {{ font-size:12.5px; color:rgba(255,255,255,.8); margin-top:2px; }}
.foot {{ text-align:center; font-size:11.5px; color:rgba(255,255,255,.6); margin-top:26px; }}
</style>
""", unsafe_allow_html=True)

# ── HERO ──
st.markdown(f"""
<div class="hero">
  <div class="logo">RANEEN<span class="dot">.</span></div>
  <div class="hero-sub">Analytics Hub</div>
  <div class="hero-tag">مركز التحليلات الموحّد — كل بياناتك في مكان واحد</div>
  <div class="hero-badge">🔴 Live · GA4 · Meta Ads · Google Ads · Executive Summary</div>
</div>
""", unsafe_allow_html=True)

# ── PAGE GRID ──
st.markdown('<div class="grid-title">اختر لوحة التحكم</div>', unsafe_allow_html=True)
st.markdown('<div class="grid-sub">اضغط على أي بطاقة للدخول إلى الصفحة</div>', unsafe_allow_html=True)

pages = [
    ("🎯", "Executive Summary",
     "الملخص التنفيذي — الربحية والأداء مقابل التارجت، MER، والتوقعات.",
     "pages/0_🎯_Executive_Summary.py", "افتح الملخص التنفيذي"),
    ("🌐", "GA4 — Web + App",
     "تحليلات Google Analytics 4 للموقع والتطبيق: الجلسات، المبيعات، القنوات.",
     "pages/1_🌐_GA4_Web_App.py", "افتح GA4"),
    ("📣", "Meta Ads",
     "أداء إعلانات Facebook و Instagram: الصرف، ROAS، الحملات.",
     "pages/2_📣_Meta_Ads.py", "افتح Meta Ads"),
    ("🔵", "Google Ads",
     "حملات Search و Performance Max: الصرف، التحويلات، ROAS.",
     "pages/3_🔵_Google_Ads.py", "افتح Google Ads"),
]

cols = st.columns(4)
for col, (icon, title, desc, path, cta) in zip(cols, pages):
    with col:
        st.markdown(
            f'<div class="pcard">'
            f'<div class="pcard-ico">{icon}</div>'
            f'<div class="pcard-t">{title}</div>'
            f'<div class="pcard-d">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.page_link(path, label=f"{cta}  ←")

# ── AUTHOR CREDIT ──
st.markdown("""
<div class="credit">
  <div class="credit-by">Created by</div>
  <div class="credit-name">Ahmed Khamis</div>
  <div class="credit-role">Head of Digital Marketing</div>
</div>
<div class="foot">© 2026 Raneen Analytics Hub · مدعوم بـ Windsor.ai + Google Sheets</div>
""", unsafe_allow_html=True)
