"""
agent/controller.py — Orchestrates the full portfolio risk analysis pipeline:
  1. Validate & normalise portfolio weights
  2. Fetch live prices (batch)
  3. Fetch 30-day price history per asset
  4. Compute risk metrics
  5. Build AI prompt
  6. Call AI decision engine
  7. Log report
"""

import json
import os
from datetime import datetime, timezone

from config import SUPPORTED_ASSETS, REPORTS_LOG_PATH, MAX_LOG_ENTRIES
from services.market_data import get_prices_batch, get_price_history
from services.risk_metrics import compute_metrics
from agent.prompt_builder import build_user_prompt
from agent.decision_engine import get_ai_risk_report


def run_analysis(portfolio_input: dict[str, float]) -> dict:
    """
    Runs the full portfolio risk analysis pipeline.

    Args:
        portfolio_input: {ticker: allocation_percentage}
                         e.g. {"BTC": 60, "ETH": 30, "SOL": 10}

    Returns:
        Complete result dict with prices, metrics, and AI report.
    """
    # ── Validate tickers ──────────────────────────────────────────────────────
    for t in portfolio_input:
        if t not in SUPPORTED_ASSETS:
            raise ValueError(f"Unsupported asset: {t}. Choose from {list(SUPPORTED_ASSETS.keys())}")

    # ── Normalise weights to fractions ────────────────────────────────────────
    total_pct = sum(portfolio_input.values())
    if total_pct <= 0:
        raise ValueError("Portfolio allocations must sum to a positive number.")
    weights = {t: v / total_pct for t, v in portfolio_input.items()}

    tickers  = list(weights.keys())
    coin_ids = [SUPPORTED_ASSETS[t] for t in tickers]

    # ── Live prices ───────────────────────────────────────────────────────────
    price_data = get_prices_batch(coin_ids)
    # Map back to ticker keys
    ticker_prices = {
        t: price_data[SUPPORTED_ASSETS[t]]
        for t in tickers
        if SUPPORTED_ASSETS[t] in price_data
    }

    # ── Portfolio total value (assume $10,000 base for illustration) ──────────
    BASE_VALUE  = 10_000
    total_value = BASE_VALUE
    portfolio   = {
        t: {
            "allocation": weights[t],
            "amount_usd": round(weights[t] * BASE_VALUE, 2),
            "price": ticker_prices[t]["price"],
            "change_24h": ticker_prices[t]["change_24h"],
        }
        for t in tickers
    }

    # ── Price histories ───────────────────────────────────────────────────────
    price_histories = {}
    for t in tickers:
        price_histories[t] = get_price_history(SUPPORTED_ASSETS[t], days=30)

    # ── Risk metrics ──────────────────────────────────────────────────────────
    metrics = compute_metrics(price_histories, weights)

    # ── AI prompt & report ────────────────────────────────────────────────────
    user_prompt = build_user_prompt(portfolio, ticker_prices, metrics, total_value)
    ai_report   = get_ai_risk_report(user_prompt)

    result = {
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "portfolio":   portfolio,
        "total_value": total_value,
        "metrics":     metrics,
        "ai_report":   ai_report,
    }

    _log_report(result)
    return result


# ── Logging ───────────────────────────────────────────────────────────────────

def _log_report(result: dict) -> None:
    os.makedirs(os.path.dirname(REPORTS_LOG_PATH), exist_ok=True)
    if os.path.exists(REPORTS_LOG_PATH):
        try:
            with open(REPORTS_LOG_PATH) as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []
    else:
        log = []
    log.append(result)
    log = log[-MAX_LOG_ENTRIES:]
    with open(REPORTS_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def load_recent_reports(n: int = 5) -> list[dict]:
    if not os.path.exists(REPORTS_LOG_PATH):
        return []
    try:
        with open(REPORTS_LOG_PATH) as f:
            log = json.load(f)
        return log[-n:][::-1]
    except (json.JSONDecodeError, IOError):
        return []
