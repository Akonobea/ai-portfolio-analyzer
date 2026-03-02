# 📊 AI-Powered Crypto Portfolio Risk Analyzer

A modular, production-style AI agent that analyzes a user-defined cryptocurrency portfolio
using live market data, quantitative risk metrics, and GPT-4o-mini reasoning.

---

## 📁 Project Structure

```
ai-portfolio-analyzer/
├── app.py                        # Streamlit UI dashboard
├── config.py                     # Centralized configuration
├── requirements.txt
├── .env                          # Local API key (never commit)
├── .streamlit/
│   └── secrets.toml              # Streamlit Cloud secrets
├── agent/
│   ├── __init__.py
│   ├── controller.py             # Orchestration pipeline
│   ├── prompt_builder.py         # Prompt construction
│   └── decision_engine.py        # OpenAI API + response parsing
├── services/
│   ├── __init__.py
│   ├── market_data.py            # CoinGecko price + history
│   └── risk_metrics.py           # Volatility, drawdown, correlation, HHI
└── data/
    └── reports_log.json          # Rolling log of AI risk reports
```

---

## ⚡ Quick Start

```bash
pip install -r requirements.txt

# Add your OpenAI key to .env
# OPENAI_API_KEY=sk-proj-...

streamlit run app.py
```

---

## ☁️ Streamlit Cloud Deployment

1. Push to GitHub (add `.env` and `.streamlit/secrets.toml` to `.gitignore`)
2. Go to share.streamlit.io → New app → select repo
3. App Settings → Secrets → paste: `OPENAI_API_KEY = "sk-proj-..."`
4. Deploy

---

## 🔢 Risk Metrics Computed

| Metric | Description |
|--------|-------------|
| Asset Volatility | Annualised std of daily returns per asset |
| Portfolio Volatility | Weighted covariance-based portfolio vol |
| Max Drawdown | Worst peak-to-trough decline (30 days) |
| HHI Concentration | Herfindahl index: 0=diversified, 1=concentrated |
| Risk Score | Composite 0–100 score (vol + drawdown + concentration) |
| Correlation Matrix | Pearson correlation of daily returns |

---

## ⚠️ Disclaimer

For educational and research purposes only. Not financial advice.
