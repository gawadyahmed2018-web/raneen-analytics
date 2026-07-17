"""
Raneen Analytics Hub — Landing Page.
The entry point of the multi-page app: big RANEEN logo, brand-red hero,
and clickable cards that navigate to each dashboard page.
"""

import streamlit as st

st.set_page_config(page_title="Raneen Analytics Hub", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

# ── Brand tokens (Raneen red) ──
R = {
    "red": "#E11D2A", "red2": "#C2101C", "red_dark": "#8A0B14",
    "ink": "#1A1A2E", "ink2": "#5B6472", "ink3": "#94A0B0",
    "line": "#EAECF0", "bg": "#FFF7F7", "card": "#FFFFFF",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family:'Inter','IBM Plex Sans Arabic',sans-serif; }}
#MainMenu, footer, header {{ visibility:hidden; }}
.block-container {{ padding:0 2rem 3rem; max-width:1300px; }}
.stApp {{ background:{R['bg']}; }}

/* ── HERO ── */
.hero {{
  background: linear-gradient(135deg, {R['red']} 0%, {R['red_dark']} 100%);
  border-radius: 0 0 40px 40px; padding: 70px 40px 80px; margin: 0 -2rem 0;
  text-align: center; position: relative; overflow: hidden;
}}
.hero::before {{
  content:''; position:absolute; top:-60%; right:-10%; width:520px; height:520px;
  background: radial-gradient(circle, rgba(255,255,255,.12) 0%, transparent 70%);
}}
.hero::after {{
  content:''; position:absolute; bottom:-70%; left:-8%; width:460px; height:460px;
  background: radial-gradient(circle, rgba(255,255,255,.08) 0%, transparent 70%);
}}
.logo {{
  font-size: 82px; font-weight: 900; color:#fff; letter-spacing:-.04em;
  line-height:1; margin-bottom:8px; position:relative; text-shadow:0 4px 24px rgba(0,0,0,.18);
}}
.logo .dot {{ color:#FFD5D8; }}
.hero-sub {{ font-size:20px; font-weight:600; color:rgba(255,255,255,.95); position:relative; letter-spacing:.02em; }}
.hero-tag {{ font-size:13.5px; color:rgba(255,255,255,.75); margin-top:10px; position:relative; }}
.hero-badge {{
  display:inline-flex; align-items:center; gap:7px; background:rgba(255,255,255,.16);
  border:1px solid rgba(255,255,255,.25); border-radius:100px; padding:6px 16px;
  font-size:12px; font-weight:600; color:#fff; margin-top:20px; position:relative; backdrop-filter:blur(6px);
}}

/* ── page cards ── */
.grid-title {{ font-size:15px; font-weight:700; color:{R['ink2']}; text-align:center; margin:44px 0 6px; letter-spacing:.02em; }}
.grid-sub {{ font-size:13px; color:{R['ink3']}; text-align:center; margin-bottom:26px; }}
.pcard {{
  background:{R['card']}; border:1px solid {R['line']}; border-radius:22px; padding:28px 26px;
  box-shadow:0 2px 8px rgba(226,29,42,.05); transition:all .2s ease; height:100%; position:relative; overflow:hidden;
}}
.pcard:hover {{ transform:translateY(-4px); box-shadow:0 16px 36px rgba(226,29,42,.14); border-color:{R['red']}; }}
.pcard-ico {{ width:54px; height:54px; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:26px; margin-bottom:16px; }}
.pcard-t {{ font-size:18px; font-weight:750; color:{R['ink']}; margin-bottom:5px; }}
.pcard-d {{ font-size:13px; color:{R['ink3']}; line-height:1.6; margin-bottom:18px; min-height:38px; }}
.pcard-cta {{ font-size:13px; font-weight:700; color:{R['red']}; display:inline-flex; align-items:center; gap:6px; }}

/* make the real page_link buttons look like part of the card */
[data-testid="stPageLink"] {{ margin-top:-6px; }}
[data-testid="stPageLink"] a {{
  background:{R['red']}; border-radius:12px; padding:11px 16px; justify-content:center;
  border:none; transition:background .2s;
}}
[data-testid="stPageLink"] a:hover {{ background:{R['red2']}; }}
[data-testid="stPageLink"] a p {{ color:#fff !important; font-weight:700 !important; font-size:13.5px !important; }}
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
    ("🎯", "#FEE4E2", "#E11D2A", "Executive Summary",
     "الملخص التنفيذي — الربحية والأداء مقابل التارجت، MER، والتوقعات.",
     "pages/0_🎯_Executive_Summary.py", "افتح الملخص التنفيذي"),
    ("🌐", "#DBEAFE", "#2E90FA", "GA4 — Web + App",
     "تحليلات Google Analytics 4 للموقع والتطبيق: الجلسات، المبيعات، القنوات.",
     "pages/1_🌐_GA4_Web_App.py", "افتح GA4"),
    ("📣", "#EDE9FE", "#7A5AF8", "Meta Ads",
     "أداء إعلانات Facebook و Instagram: الصرف، ROAS، الحملات.",
     "pages/2_📣_Meta_Ads.py", "افتح Meta Ads"),
    ("🔵", "#D1E9FF", "#175CD3", "Google Ads",
     "حملات Search و Performance Max: الصرف، التحويلات، ROAS.",
     "pages/3_🔵_Google_Ads.py", "افتح Google Ads"),
]

cols = st.columns(4)
for col, (icon, soft, color, title, desc, path, cta) in zip(cols, pages):
    with col:
        st.markdown(
            f'<div class="pcard">'
            f'<div class="pcard-ico" style="background:{soft};color:{color}">{icon}</div>'
            f'<div class="pcard-t">{title}</div>'
            f'<div class="pcard-d">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.page_link(path, label=f"{cta}  ←")

st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
st.markdown(
    f'<div style="text-align:center;font-size:12px;color:{R["ink3"]};">'
    f'© 2026 Raneen Analytics Hub · مدعوم بـ Windsor.ai + Google Sheets</div>',
    unsafe_allow_html=True,
)
