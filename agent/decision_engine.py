"""
agent/decision_engine.py — Calls OpenAI and parses the structured JSON risk report.
"""

import json
import openai
from config import get_openai_key, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from agent.prompt_builder import SYSTEM_PROMPT


def get_ai_risk_report(user_prompt: str) -> dict:
    """
    Sends the portfolio prompt to GPT-4o-mini and returns a validated risk report.

    Returns:
        dict with keys: risk_score, risk_label, diversification_assessment,
                        key_risks, rebalancing_suggestions, summary
    """
    client = openai.OpenAI(api_key=get_openai_key())

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    try:
        report = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON: {raw}") from exc

    required = {
        "risk_score", "risk_label", "diversification_assessment",
        "key_risks", "rebalancing_suggestions", "summary"
    }
    missing = required - report.keys()
    if missing:
        raise ValueError(f"LLM response missing fields: {missing}")

    report["risk_score"] = int(report["risk_score"])
    return report
