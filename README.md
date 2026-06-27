# Raneen Analytics — Web + App Combined Dashboard

Streamlit dashboard that connects to **Google Analytics 4** via **Windsor.ai**
to show combined analytics for both:

- 🌐 **Raneen.com** (Web)
- 📱 **Raneen Mobile APP** (App)

## Features

- **Source filter** — view Web only, App only, or both combined
- **Overview** — KPIs, Revenue trends, New vs Returning, Web vs App split
- **Funnel** — Full sales funnel with drop-off analysis, by source
- **Traffic** — Channel efficiency (CVR, Rev/Session)
- **Devices** — Mobile vs Desktop vs Tablet breakdown
- **E-Commerce** — Top products, categories, cart rates
- **Campaigns** — Google Ads + Meta campaign performance

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/raneen-analytics.git
cd raneen-analytics
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run locally
```bash
streamlit run app.py
```

### 4. Deploy on Streamlit Cloud
1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo → select `app.py`
4. Deploy

## How Web vs App separation works

`windsor.py` queries Windsor.ai **twice** per data request — once filtered by
`account_name=Raneen.com` and once by `account_name=Raneen Mobile APP (Latest)`.
Each result set gets tagged with a `source` column (`"web"` or `"app"`), then
combined into one DataFrame. The sidebar **Data Source** radio lets you filter
to web-only, app-only, or both combined everywhere in the dashboard.

## Stack

- **Streamlit** — UI framework
- **Plotly** — Interactive charts
- **Windsor.ai API** — GA4 connector (2 accounts: Web + App)
- **Pandas** — Data processing
