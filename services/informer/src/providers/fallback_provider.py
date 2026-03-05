"""
fallback_provider.py — Alpha Vantage REST API fallback when yfinance is unavailable.
Respects the free-tier limit of 5 requests/minute (12s inter-request interval).
"""
import logging
import threading
import time
from typing import Any

import requests
import pandas as pd

from .base_provider import BaseProvider
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

_AV_BASE = "https://www.alphavantage.co/query"

# Alpha Vantage free tier: 5 req/min → enforce 12s minimum gap between calls
_AV_MIN_INTERVAL = 12.0
_last_call_time: float = 0.0
_av_lock = threading.Lock()


def _av_rate_wait() -> None:
    """Block until the minimum inter-request interval has elapsed (thread-safe)."""
    global _last_call_time
    with _av_lock:
        elapsed = time.monotonic() - _last_call_time
        wait = max(0.0, _AV_MIN_INTERVAL - elapsed)
    # Sleep OUTSIDE the lock to avoid blocking other threads
    if wait > 0:
        logger.debug("Alpha Vantage rate limit — sleeping %.1fs", wait)
        time.sleep(wait)
    with _av_lock:
        _last_call_time = time.monotonic()


class AlphaVantageProvider(BaseProvider):
    """
    Uses Alpha Vantage REST endpoints as a fallback data source.
    Requires ALPHA_VANTAGE_KEY set in settings / environment.
    """

    def __init__(self, api_key: str, timeout: int = 30) -> None:
        if not api_key:
            logger.warning("AlphaVantageProvider created with empty API key — calls will fail")
        self._api_key = api_key
        self._timeout = timeout

    # ─── internal helpers ─────────────────────────────────────────────────────

    def _get(self, params: dict) -> dict[str, Any]:
        """Execute a rate-limited GET to Alpha Vantage and return the JSON body."""
        _av_rate_wait()
        params["apikey"] = self._api_key
        resp = requests.get(_AV_BASE, params=params, timeout=self._timeout)
        resp.raise_for_status()
        data = resp.json()
        if "Note" in data or "Information" in data:
            # Rate-limit warning / premium endpoint notice from AV
            msg = data.get("Note") or data.get("Information", "")
            raise RuntimeError(f"Alpha Vantage API limit: {msg}")
        return data

    # ─── metadata ─────────────────────────────────────────────────────────────

    @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
    def get_stock_metadata(self, symbol: str) -> dict:
        """Fetch company overview from AV OVERVIEW endpoint."""
        data = self._get({"function": "OVERVIEW", "symbol": symbol})
        return {
            "symbol": symbol.upper(),
            "name": data.get("Name", symbol),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "exchange": data.get("Exchange"),
            "country": data.get("Country", "US"),
            "currency": data.get("Currency", "USD"),
            "market_cap": _int_or_none(data.get("MarketCapitalization")),
            "description": data.get("Description"),
            "website": None,
            "is_active": True,
        }

    # ─── OHLCV history ────────────────────────────────────────────────────────

    @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
    def get_historical_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Fetch daily adjusted OHLCV from TIME_SERIES_DAILY_ADJUSTED (full output).
        Filters rows to [start_date, end_date] range.
        """
        data = self._get({
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "full",
        })

        ts: dict = data.get("Time Series (Daily)", {})
        if not ts:
            logger.warning("Alpha Vantage returned no time-series data for %s", symbol)
            return pd.DataFrame()

        rows = []
        for date_str, bar in ts.items():
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            rows.append({
                "time": date_str,
                "open": float(bar["1. open"]),
                "high": float(bar["2. high"]),
                "low": float(bar["3. low"]),
                "close": float(bar["4. close"]),
                "volume": int(bar["6. volume"]),
                "adjusted_close": float(bar["5. adjusted close"]),
            })

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows).sort_values("time")
        logger.debug("Fetched %d OHLCV bars for %s from Alpha Vantage", len(df), symbol)
        return df

    # ─── financial reports ────────────────────────────────────────────────────

    @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
    def get_financial_reports(self, symbol: str) -> list[dict]:
        """
        Fetch annual/quarterly income statement from Alpha Vantage INCOME_STATEMENT.
        Only income data is available on the free tier; balance sheet / cash flow
        fields are left as None.
        """
        data = self._get({"function": "INCOME_STATEMENT", "symbol": symbol})
        reports: list[dict] = []

        for report_type, key in (("Annual", "annualReports"), ("Quarterly", "quarterlyReports")):
            for item in data.get(key, []):
                reports.append({
                    "report_date": item.get("fiscalDateEnding"),
                    "report_type": report_type,
                    "revenue": _float_or_none(item.get("totalRevenue")),
                    "gross_profit": _float_or_none(item.get("grossProfit")),
                    "operating_income": _float_or_none(item.get("operatingIncome")),
                    "net_income": _float_or_none(item.get("netIncome")),
                    "eps": _float_or_none(item.get("reportedEPS")),
                    # Not available on free-tier INCOME_STATEMENT endpoint
                    "total_assets": None,
                    "total_liabilities": None,
                    "shareholders_equity": None,
                    "book_value_per_share": None,
                    "operating_cash_flow": None,
                    "free_cash_flow": None,
                    "capex": None,
                    "shares_outstanding": None,
                    "debt_to_equity": None,
                    "current_ratio": None,
                    "roe": None,
                    "roa": None,
                })

        logger.debug("Fetched %d financial reports for %s from Alpha Vantage", len(reports), symbol)
        return reports


# ─── helpers ──────────────────────────────────────────────────────────────────

def _float_or_none(val) -> float | None:
    try:
        return float(val) if val not in (None, "None", "N/A", "") else None
    except (TypeError, ValueError):
        return None


def _int_or_none(val) -> int | None:
    try:
        return int(val) if val not in (None, "None", "N/A", "") else None
    except (TypeError, ValueError):
        return None
