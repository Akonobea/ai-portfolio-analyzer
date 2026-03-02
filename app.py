"""
app.py — Streamlit UI for the AI-Powered Crypto Portfolio Risk Analyzer.

Run locally:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
from agent.controller import run_analysis, load_recent_reports
from config import SUPPORTED_ASSETS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Portfolio Risk Analyzer",
    page_icon="📊",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    .risk-badge-Low    { background:#0d3b26; color:#00e676; padding:6px 18px; border-radius:4px; font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:1.1rem; display:inline-block; }
    .risk-badge-Medium { background:#3b2a00; color:#ffb300; padding:6px 18px; border-radius:4px; font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:1.1rem; display:inline-block; }
    .risk-badge-High   { background:#3b0d0d; color:#ff5252; padding:6px 18px; border-radius:4px; font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:1.1rem; display:inline-block; }

    .metric-card { background:#111827; border:1px solid #1f2937; border-radius:8px; padding:16px 20px; }
    .mono { font-family:'IBM Plex Mono', monospace; }

    div[data-testid="stMetricValue"] { font-family:'IBM Plex Mono', monospace; font-size:1.4rem; }
    .stButton>button { font-family:'IBM Plex Mono', monospace; font-weight:600; letter-spacing:0.05em; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 AI Crypto Portfolio Risk Analyzer")
st.caption("Weighted volatility • Max drawdown • Correlation analysis • GPT-4o-mini risk report")
st.divider()

# ── Sidebar — Portfolio Builder ────────────────────────────────────────────────
with st.sidebar:
    st.header("🏗️ Build Your Portfolio")
    st.caption("Allocations auto-normalise to 100%.")

    asset_list = list(SUPPORTED_ASSETS.keys())
    selected_assets = st.multiselect(
        "Select Assets",
        options=asset_list,
        default=["BTC", "ETH", "SOL"],
        max_selections=6,
    )

    allocations = {}
    if selected_assets:
        st.markdown("**Set Allocations (%)**")
        for asset in selected_assets:
            allocations[asset] = st.slider(
                asset, min_value=1, max_value=100,
                value={"BTC": 50, "ETH": 30, "SOL": 10}.get(asset, 15),
                step=1,
            )

        total = sum(allocations.values())
        normalised = {t: round(v / total * 100, 1) for t, v in allocations.items()}

        st.markdown("---")
        st.markdown("**Normalised Weights**")
        for t, w in normalised.items():
            st.markdown(f"`{t}` — **{w}%**")

    st.markdown("---")
    st.caption("Data: CoinGecko (free) • AI: GPT-4o-mini")

# ── Main — Run button ──────────────────────────────────────────────────────────
if not selected_assets:
    st.info("👈 Select at least one asset in the sidebar to get started.")
    st.stop()

col_btn, _ = st.columns([1, 4])
with col_btn:
    run_clicked = st.button("▶ Analyze Portfolio", type="primary", use_container_width=True)

# ── Analysis ───────────────────────────────────────────────────────────────────
if run_clicked:
    with st.spinner("Fetching market data and computing risk metrics…"):
        try:
            result = run_analysis(allocations)
        except Exception as exc:
            st.error(f"❌ Analysis error: {exc}")
            st.stop()

    report  = result["ai_report"]
    metrics = result["metrics"]
    port    = result["portfolio"]

    risk_label = report["risk_label"]
    risk_color = {"Low": "#00e676", "Medium": "#ffb300", "High": "#ff5252"}.get(risk_label, "#fff")

    st.subheader("📋 Portfolio Snapshot")

    # ── Asset table ────────────────────────────────────────────────────────────
    rows = []
    for t, d in port.items():
        rows.append({
            "Asset": t,
            "Allocation": f"{d['allocation']*100:.1f}%",
            "USD Value": f"${d['amount_usd']:,.2f}",
            "Price": f"${d['price']:,.2f}",
            "24h Change": f"{d['change_24h']:+.2f}%",
            "Volatility (ann.)": f"{metrics['volatilities'][t]}%",
            "Max Drawdown": f"{metrics['max_drawdowns'][t]}%",
        })
    st.dataframe(pd.DataFrame(rows).set_index("Asset"), use_container_width=True)

    st.divider()
    st.subheader("⚠️ Risk Assessment")

    # ── KPI row ────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk Score", f"{report['risk_score']} / 100")
    c2.metric("Portfolio Volatility", f"{metrics['portfolio_volatility']}%")
    c3.metric("Concentration (HHI)", f"{metrics['hhi']:.3f}")
    c4.metric("Diversification", report["diversification_assessment"])

    # Risk badge
    st.markdown(
        f'<div class="risk-badge-{risk_label}">● {risk_label} Risk</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Key risks + suggestions ────────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.subheader("🔍 Key Risks")
        for r in report["key_risks"]:
            st.markdown(f"- {r}")

    with right:
        st.subheader("♻️ Rebalancing Suggestions")
        for s in report["rebalancing_suggestions"]:
            st.markdown(f"- {s}")

    st.divider()

    # ── Correlation matrix ─────────────────────────────────────────────────────
    tickers = metrics["tickers"]
    if len(tickers) > 1:
        st.subheader("📐 Asset Correlation Matrix (30-day)")
        corr_df = pd.DataFrame(
            {a: {b: metrics["correlation"].get(a, {}).get(b, 1.0) for b in tickers} for a in tickers}
        )
        st.dataframe(corr_df.style.background_gradient(cmap="RdYlGn", vmin=-1, vmax=1).format("{:.3f}"),
                     use_container_width=True)
        st.caption("Green = low correlation (better diversification) | Red = high correlation (concentrated risk)")

    st.divider()

    # ── AI summary ────────────────────────────────────────────────────────────
    st.subheader("🧠 AI Risk Narrative")
    st.info(report["summary"])

# ── Recent reports log ─────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Recent Analysis History")
recent = load_recent_reports(5)

if not recent:
    st.caption("No reports logged yet. Run an analysis to get started.")
else:
    for entry in recent:
        r   = entry["ai_report"]
        ts  = entry["timestamp"][:19].replace("T", " ")
        tks = ", ".join(entry["portfolio"].keys())
        risk_icon = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(r["risk_label"], "⚪")

        with st.expander(
            f"{risk_icon} [{ts} UTC]  {tks}  —  Risk: {r['risk_label']}  |  Score: {r['risk_score']}/100"
        ):
            st.markdown(f"**Diversification:** {r['diversification_assessment']}")
            st.markdown(f"**Summary:** {r['summary']}")
            st.markdown("**Suggestions:** " + " • ".join(r["rebalancing_suggestions"]))
