"""
hybrid_provider.py — Orchestrates DB-cache → yfinance → Alpha Vantage data flow.
Logs which provider served each request; falls back gracefully on errors.
"""
import logging
from datetime import datetime, timedelta, date
from typing import Optional

import pandas as pd

from .base_provider import BaseProvider
from .yfinance_provider import YFinanceProvider
from .fallback_provider import AlphaVantageProvider

logger = logging.getLogger(__name__)

# Metadata cache TTL: re-fetch from provider after this many days
_METADATA_CACHE_DAYS = 7


class HybridProvider(BaseProvider):
    """
    Data-access orchestrator:

      1. Check DB cache (via repositories injected through db_pool).
      2. Try yfinance (primary).
      3. Fall back to Alpha Vantage on yfinance failure.

    Repositories are injected lazily so the HybridProvider can be constructed
    before they are wired up (server.py dependency order).
    """

    def __init__(self, settings, db_pool) -> None:
        self._settings = settings
        self._db = db_pool
        self._yfinance = YFinanceProvider()
        self._av = AlphaVantageProvider(api_key=settings.alpha_vantage_key)

        # Populated by server.py after all repos are constructed
        self.stock_repo = None
        self.ohlcv_repo = None
        self.financial_repo = None

    # ─── metadata ─────────────────────────────────────────────────────────────

    def get_stock_metadata(self, symbol: str) -> dict:
        """
        Return metadata:
          - DB cache if last updated < _METADATA_CACHE_DAYS ago.
          - yfinance otherwise; persist result to DB.
          - Alpha Vantage if yfinance fails.
        """
        # 1. Check DB cache freshness
        if self.stock_repo:
            cached = self.stock_repo.get_by_symbol(symbol)
            if cached and _is_fresh(cached.get("updated_at"), days=_METADATA_CACHE_DAYS):
                logger.debug("Metadata for %s served from DB cache", symbol)
                return cached

        # 2. yfinance (primary)
        try:
            data = self._yfinance.get_stock_metadata(symbol)
            if self.stock_repo:
                self.stock_repo.upsert(data)
            logger.info("Metadata for %s fetched from yfinance", symbol)
            return data
        except Exception as yf_err:
            logger.warning("yfinance metadata failed for %s: %s — trying Alpha Vantage", symbol, yf_err)

        # 3. Alpha Vantage fallback
        try:
            data = self._av.get_stock_metadata(symbol)
            if self.stock_repo:
                self.stock_repo.upsert(data)
            logger.info("Metadata for %s fetched from Alpha Vantage (fallback)", symbol)
            return data
        except Exception as av_err:
            logger.error("Alpha Vantage metadata also failed for %s: %s", symbol, av_err)
            raise RuntimeError(f"All metadata providers failed for {symbol}") from av_err

    # ─── OHLCV history ────────────────────────────────────────────────────────

    def get_historical_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Return OHLCV data:
          - DB rows for the requested range (if complete).
          - Fetch only the missing date range from provider; persist to DB.

        Uses yfinance → Alpha Vantage fallback.
        """
        stock_id: Optional[int] = self._resolve_stock_id(symbol)

        # 1. DB cache — check what's already stored
        if stock_id and self.ohlcv_repo:
            cached_df = _rows_to_df(
                self.ohlcv_repo.get_history(stock_id, start_date, end_date)
            )
            if not cached_df.empty and _covers_range(cached_df, start_date, end_date):
                logger.debug("OHLCV for %s served fully from DB cache", symbol)
                return cached_df

        # 2. Fetch from provider (full range; let DB upsert handle dedup)
        df = self._fetch_ohlcv_with_fallback(symbol, start_date, end_date)

        # 3. Persist to DB
        if not df.empty and stock_id and self.ohlcv_repo:
            candles = df.to_dict("records")
            self.ohlcv_repo.bulk_upsert(stock_id, candles)

        return df

    def _fetch_ohlcv_with_fallback(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Try yfinance first; fall back to Alpha Vantage on any error."""
        try:
            df = self._yfinance.get_historical_ohlcv(symbol, start_date, end_date)
            if not df.empty:
                logger.info("OHLCV for %s fetched from yfinance (%d bars)", symbol, len(df))
                return df
            logger.warning("yfinance returned empty OHLCV for %s", symbol)
        except Exception as yf_err:
            logger.warning("yfinance OHLCV failed for %s: %s", symbol, yf_err)

        try:
            df = self._av.get_historical_ohlcv(symbol, start_date, end_date)
            logger.info(
                "OHLCV for %s fetched from Alpha Vantage fallback (%d bars)",
                symbol, len(df),
            )
            return df
        except Exception as av_err:
            logger.error("Alpha Vantage OHLCV also failed for %s: %s", symbol, av_err)
            return pd.DataFrame()

    # ─── financial reports ────────────────────────────────────────────────────

    def get_financial_reports(self, symbol: str) -> list[dict]:
        """
        Return financial reports:
          - DB cache if present (reports are stable; re-use until new quarter).
          - yfinance → Alpha Vantage fallback otherwise.
        """
        stock_id = self._resolve_stock_id(symbol)

        # 1. DB cache — return if we have both annual and quarterly reports
        if stock_id and self.financial_repo:
            cached_annual = self.financial_repo.get_history(stock_id, "Annual", years_back=10)
            cached_quarterly = self.financial_repo.get_history(stock_id, "Quarterly", years_back=10)
            if cached_annual or cached_quarterly:
                cached = (cached_annual or []) + (cached_quarterly or [])
                logger.debug("Financial reports for %s served from DB cache", symbol)
                return cached

        # 2. yfinance
        try:
            reports = self._yfinance.get_financial_reports(symbol)
            if reports and stock_id and self.financial_repo:
                for r in reports:
                    self.financial_repo.upsert(stock_id, r)
            logger.info("Financial reports for %s fetched from yfinance (%d)", symbol, len(reports))
            return reports
        except Exception as yf_err:
            logger.warning("yfinance financials failed for %s: %s", symbol, yf_err)

        # 3. Alpha Vantage
        try:
            reports = self._av.get_financial_reports(symbol)
            if reports and stock_id and self.financial_repo:
                for r in reports:
                    self.financial_repo.upsert(stock_id, r)
            logger.info(
                "Financial reports for %s fetched from Alpha Vantage (%d)", symbol, len(reports)
            )
            return reports
        except Exception as av_err:
            logger.error("Alpha Vantage financials also failed for %s: %s", symbol, av_err)
            return []

    # ─── helpers ──────────────────────────────────────────────────────────────

    def _resolve_stock_id(self, symbol: str) -> Optional[int]:
        """Return stock.id from DB, or None if repo not wired / record not found."""
        if self.stock_repo:
            row = self.stock_repo.get_by_symbol(symbol)
            if row:
                return row["id"]
        return None


# ─── module-level helpers ─────────────────────────────────────────────────────

def _is_fresh(updated_at, days: int) -> bool:
    """Return True when `updated_at` is within the last `days` days."""
    if updated_at is None:
        return False
    if isinstance(updated_at, str):
        try:
            updated_at = datetime.fromisoformat(updated_at)
        except ValueError:
            return False
    # Make timezone-naive for comparison
    if hasattr(updated_at, "tzinfo") and updated_at.tzinfo is not None:
        from datetime import timezone
        now = datetime.now(timezone.utc)
    else:
        now = datetime.utcnow()
    return (now - updated_at) < timedelta(days=days)


def _rows_to_df(rows: list[dict]) -> pd.DataFrame:
    """Convert a list of ohlcv row dicts to a DataFrame."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")
    return df


def _covers_range(df: pd.DataFrame, start_date: str, end_date: str) -> bool:
    """
    Return True if the DataFrame has data covering start_date to end_date.
    Tolerates missing weekends/holidays by checking first/last date only.
    """
    try:
        times = sorted(df["time"].tolist())
        return times[0] <= start_date and times[-1] >= end_date
    except Exception:
        return False
