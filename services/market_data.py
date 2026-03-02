"""
services/market_data.py — Fetches live prices and 30-day history from CoinGecko.
Uses /market_chart (free tier safe) instead of /ohlc.
"""

import requests
import pandas as pd
from config import COINGECKO_BASE

_SUPPORTED_DAYS = [1, 7, 14, 30, 90, 180, 365]


def _snap_days(days: int) -> int:
    return min(_SUPPORTED_DAYS, key=lambda x: abs(x - days))


def get_prices_batch(coin_ids: list[str]) -> dict:
    """
    Fetch current USD prices for multiple coins in one API call.

    Returns:
        dict mapping coin_id -> current USD price
    """
    url = f"{COINGECKO_BASE}/simple/price"
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        cid: {
            "price": data[cid]["usd"],
            "change_24h": data[cid].get("usd_24h_change", 0.0),
        }
        for cid in coin_ids
        if cid in data
    }


def get_price_history(coin_id: str, days: int = 30) -> pd.Series:
    """
    Returns a daily closing price Series for a coin over `days` days.

    Args:
        coin_id: CoinGecko identifier (e.g. 'bitcoin').
        days:    Number of historical days.

    Returns:
        pd.Series of closing prices indexed by date.
    """
    days = _snap_days(days)
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    prices = resp.json().get("prices", [])
    df = pd.DataFrame(prices, columns=["ts_ms", "close"])
    df["date"] = pd.to_datetime(df["ts_ms"], unit="ms").dt.normalize()
    df = df.drop_duplicates("date").set_index("date")["close"]
    return df.sort_index()
