"""
config.py — Centralized configuration for the AI Portfolio Risk Analyzer.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass


def get_openai_key() -> str:
    """Three-tier key resolution: .env -> env var -> st.secrets"""
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    raise ValueError(
        "OPENAI_API_KEY not found.\n"
        "Local:  add to .env  ->  OPENAI_API_KEY=sk-...\n"
        "Cloud:  Streamlit Cloud -> App Settings -> Secrets"
    )


# ── Supported assets ──────────────────────────────────────────────────────────
SUPPORTED_ASSETS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "DOGE": "dogecoin",
}

# ── API ───────────────────────────────────────────────────────────────────────
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# ── LLM ───────────────────────────────────────────────────────────────────────
LLM_MODEL       = "gpt-4o-mini"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS  = 700

# ── Risk thresholds ───────────────────────────────────────────────────────────
LOW_RISK_THRESHOLD    = 35
MEDIUM_RISK_THRESHOLD = 65

# ── Logging ───────────────────────────────────────────────────────────────────
REPORTS_LOG_PATH = "data/reports_log.json"
MAX_LOG_ENTRIES  = 50
