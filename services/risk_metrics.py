"""
services/risk_metrics.py — Computes portfolio-level risk metrics from price history.

Metrics calculated:
  - Individual asset volatility (annualised std of daily returns)
  - Weighted portfolio volatility
  - Max drawdown per asset
  - Pearson correlation matrix
  - Concentration (Herfindahl index)
  - Overall portfolio risk score (0-100)
"""

import numpy as np
import pandas as pd
from config import LOW_RISK_THRESHOLD, MEDIUM_RISK_THRESHOLD


def compute_metrics(price_histories: dict[str, pd.Series], weights: dict[str, float]) -> dict:
    """
    Computes full portfolio risk metrics.

    Args:
        price_histories: {ticker: pd.Series of closing prices}
        weights:         {ticker: allocation fraction} — must sum to 1.0

    Returns:
        dict with all computed metrics ready for the AI prompt and UI.
    """
    tickers = list(weights.keys())

    # ── Daily returns ─────────────────────────────────────────────────────────
    returns = {}
    for t in tickers:
        s = price_histories[t]
        returns[t] = s.pct_change().dropna()

    returns_df = pd.DataFrame(returns).dropna()

    # ── Per-asset volatility (annualised) ─────────────────────────────────────
    volatilities = {
        t: round(float(returns_df[t].std() * np.sqrt(365) * 100), 2)
        for t in tickers
    }

    # ── Weighted portfolio volatility ─────────────────────────────────────────
    w = np.array([weights[t] for t in tickers])
    cov_matrix = returns_df.cov() * 365
    port_variance = float(w @ cov_matrix.values @ w)
    port_volatility = round(float(np.sqrt(port_variance) * 100), 2)

    # ── Max drawdown per asset ────────────────────────────────────────────────
    max_drawdowns = {}
    for t in tickers:
        s = price_histories[t]
        rolling_max = s.cummax()
        drawdown = ((s - rolling_max) / rolling_max * 100)
        max_drawdowns[t] = round(float(drawdown.min()), 2)

    # ── Correlation matrix ────────────────────────────────────────────────────
    corr = returns_df.corr().round(3)
    corr_dict = corr.to_dict()

    # ── Concentration (Herfindahl index: 0=diversified, 1=concentrated) ──────
    hhi = round(float(sum(v ** 2 for v in weights.values())), 4)

    # ── Portfolio risk score (0-100) ──────────────────────────────────────────
    # Composite: 50% volatility component + 30% drawdown + 20% concentration
    vol_score        = min(port_volatility / 1.5, 100)      # normalise ~150% vol = 100
    drawdown_score   = min(abs(min(max_drawdowns.values())) / 0.9, 100)
    concentration_score = hhi * 100

    risk_score = round(
        0.5 * vol_score + 0.3 * drawdown_score + 0.2 * concentration_score, 1
    )
    risk_score = min(max(risk_score, 0), 100)

    # ── Risk label ────────────────────────────────────────────────────────────
    if risk_score <= LOW_RISK_THRESHOLD:
        risk_label = "Low"
    elif risk_score <= MEDIUM_RISK_THRESHOLD:
        risk_label = "Medium"
    else:
        risk_label = "High"

    return {
        "tickers": tickers,
        "weights": weights,
        "volatilities": volatilities,
        "portfolio_volatility": port_volatility,
        "max_drawdowns": max_drawdowns,
        "correlation": corr_dict,
        "hhi": hhi,
        "risk_score": risk_score,
        "risk_label": risk_label,
    }
