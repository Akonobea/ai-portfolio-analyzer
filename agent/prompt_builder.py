"""
agent/prompt_builder.py — Builds system and user prompts for the portfolio AI agent.
"""

SYSTEM_PROMPT = """You are a senior quantitative risk analyst specializing in digital asset portfolios.
Your job is to analyze a crypto portfolio's risk metrics and return a structured, data-driven risk report.

Rules:
- Be precise and analytical. Cite specific numbers from the data.
- Return ONLY a valid JSON object — no markdown, no text outside JSON.
- risk_score must be an integer 0-100.
- risk_label must be exactly one of: "Low", "Medium", "High".
- rebalancing_suggestions must be a list of 2-4 actionable strings.
- key_risks must be a list of 2-4 short strings.
- diversification_assessment must be one of: "Well Diversified", "Moderately Diversified", "Concentrated".

Required JSON schema:
{
  "risk_score": <0-100>,
  "risk_label": "<Low|Medium|High>",
  "diversification_assessment": "<Well Diversified|Moderately Diversified|Concentrated>",
  "key_risks": ["<risk1>", "<risk2>"],
  "rebalancing_suggestions": ["<suggestion1>", "<suggestion2>"],
  "summary": "<3-4 sentence portfolio risk narrative>"
}"""


def build_user_prompt(
    portfolio: dict,
    current_prices: dict,
    metrics: dict,
    total_value: float,
) -> str:
    """
    Constructs the structured user prompt for the AI agent.

    Args:
        portfolio:      {ticker: {"allocation": float, "amount_usd": float}}
        current_prices: {coin_id: {"price": float, "change_24h": float}}
        metrics:        Output from risk_metrics.compute_metrics()
        total_value:    Total portfolio USD value

    Returns:
        Formatted prompt string.
    """
    weights   = metrics["weights"]
    tickers   = metrics["tickers"]

    # Build per-asset table
    asset_lines = []
    for t in tickers:
        w    = weights[t] * 100
        vol  = metrics["volatilities"][t]
        dd   = metrics["max_drawdowns"][t]
        asset_lines.append(
            f"  {t}: {w:.1f}% allocation | Volatility: {vol}% | Max Drawdown: {dd}%"
        )
    assets_text = "\n".join(asset_lines)

    # Correlation summary (highest pairs)
    corr = metrics["correlation"]
    pairs = []
    for i, a in enumerate(tickers):
        for b in tickers[i + 1:]:
            pairs.append((a, b, corr.get(a, {}).get(b, 0)))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    corr_lines = [f"  {a}/{b}: {c:.3f}" for a, b, c in pairs[:4]]
    corr_text = "\n".join(corr_lines) if corr_lines else "  N/A"

    prompt = f"""Analyze the following crypto portfolio and return your structured risk report as JSON.

## Portfolio Overview
- Total Value:            ${total_value:,.2f} USD
- Number of Assets:       {len(tickers)}
- Concentration (HHI):    {metrics['hhi']} (0=diversified, 1=concentrated)

## Asset Allocations & Risk
{assets_text}

## Portfolio-Level Metrics
- Weighted Portfolio Volatility (annualised): {metrics['portfolio_volatility']}%
- Computed Risk Score:                        {metrics['risk_score']} / 100
- Computed Risk Label:                        {metrics['risk_label']}

## Asset Correlations (top pairs)
{corr_text}

Based on all of the above, provide your structured JSON risk report now."""

    return prompt
