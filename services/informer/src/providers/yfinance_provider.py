"""
yfinance_provider.py — Primary stock data source using the yfinance library.
Rate-limited to ~1 req/sec; retries with exponential backoff on transient errors.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from .base_provider import BaseProvider
from utils.rate_limiter import RateLimiter
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Shared rate limiter: max 1 call/second across all YFinanceProvider instances
_rate_limiter = RateLimiter(max_calls=1, period=1.0)


class YFinanceProvider(BaseProvider):
    """
    Wraps yfinance for stock metadata, OHLCV history, and financial reports.
    All public methods apply rate limiting and exponential-backoff retries.
    """

    # ─── metadata ─────────────────────────────────────────────────────────────

    @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
    def get_stock_metadata(self, symbol: str) -> dict:
        """
        Fetch static stock info via yf.Ticker.info.
        Maps yfinance field names to our schema column names.
        """
        with _rate_limiter:
            ticker = yf.Ticker(symbol)
            info: dict[str, Any] = ticker.info or {}

        metadata = {
            "symbol": symbol.upper(),
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "exchange": info.get("exchange"),
            "country": info.get("country", "US"),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap"),
            "description": info.get("longBusinessSummary"),
            "website": info.get("website"),
            "is_active": True,
        }
        logger.debug("Fetched metadata for %s via yfinance", symbol)
        return metadata

    # ─── OHLCV history ────────────────────────────────────────────────────────

    @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
    def get_historical_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Download daily OHLCV bars and normalise column names to match our schema.

        Returns:
            DataFrame with columns: time, open, high, low, close, volume,
            adjusted_close.  Index is reset (integer).  Empty on failure.
        """
        with _rate_limiter:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval="1d",
                auto_adjust=False,  # keep raw + Adj Close separately
            )

        if df.empty:
            logger.warning("yfinance returned empty OHLCV for %s (%s→%s)", symbol, start_date, end_date)
            return pd.DataFrame()

        # Normalise column names to lowercase schema names
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Adj Close": "adjusted_close",
        })

        # Ensure the index (DatetimeIndex) becomes the `time` column as ISO string
        df = df.reset_index()
        df = df.rename(columns={"Date": "time", "Datetime": "time"})
        df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")

        # Keep only schema columns; add adjusted_close if missing
        keep_cols = ["time", "open", "high", "low", "close", "volume"]
        if "adjusted_close" in df.columns:
            keep_cols.append("adjusted_close")
        else:
            df["adjusted_close"] = None
            keep_cols.append("adjusted_close")

        logger.debug(
            "Fetched %d OHLCV bars for %s (%s→%s)", len(df), symbol, start_date, end_date
        )
        return df[keep_cols]

    # ─── financial reports ────────────────────────────────────────────────────

    @retry_with_backoff(max_retries=3, backoff_factor=2.0, exceptions=(Exception,))
    def get_financial_reports(self, symbol: str) -> list[dict]:
        """
        Fetch annual and quarterly financial statements and merge into report dicts.

        Combines income_stmt + balance_sheet + cashflow for each period.
        Returns list sorted by (report_type, report_date DESC).
        """
        # yfinance makes multiple HTTP calls internally for each statement.
        # Consume rate-limit tokens for each API call to avoid burst requests.
        with _rate_limiter:
            ticker = yf.Ticker(symbol)
            income_annual = ticker.income_stmt
        with _rate_limiter:
            income_qtr = ticker.quarterly_income_stmt
        with _rate_limiter:
            balance_annual = ticker.balance_sheet
        with _rate_limiter:
            balance_qtr = ticker.quarterly_balance_sheet
        with _rate_limiter:
            cash_annual = ticker.cashflow
        with _rate_limiter:
            cash_qtr = ticker.quarterly_cashflow

        reports: list[dict] = []

        def _safe_val(df: pd.DataFrame, row: str, col) -> float | None:
            """Extract a scalar from a DataFrame cell; return None on any error."""
            try:
                if df is None or df.empty or row not in df.index:
                    return None
                v = df.loc[row, col]
                return None if pd.isna(v) else float(v)
            except Exception:
                return None

        def _build_reports(inc, bal, csh, report_type: str) -> list[dict]:
            """Merge three statement DataFrames into one report dict per period."""
            if inc is None or inc.empty:
                return []
            result = []
            for col in inc.columns:
                # col is a pandas Timestamp
                try:
                    report_date = col.strftime("%Y-%m-%d")
                except AttributeError:
                    report_date = str(col)[:10]

                report = {
                    "report_date": report_date,
                    "report_type": report_type,
                    # Income statement
                    "revenue": _safe_val(inc, "Total Revenue", col),
                    "gross_profit": _safe_val(inc, "Gross Profit", col),
                    "operating_income": _safe_val(inc, "Operating Income", col),
                    "net_income": _safe_val(inc, "Net Income", col),
                    "eps": _safe_val(inc, "Basic EPS", col),
                    # Balance sheet
                    "total_assets": _safe_val(bal, "Total Assets", col),
                    "total_liabilities": _safe_val(bal, "Total Liabilities Net Minority Interest", col),
                    "shareholders_equity": _safe_val(bal, "Stockholders Equity", col),
                    "book_value_per_share": None,  # calculated below if possible
                    # Cash flow
                    "operating_cash_flow": _safe_val(csh, "Operating Cash Flow", col),
                    "free_cash_flow": _safe_val(csh, "Free Cash Flow", col),
                    "capex": _safe_val(csh, "Capital Expenditure", col),
                    # Derived ratios (best effort)
                    "shares_outstanding": None,
                    "debt_to_equity": None,
                    "current_ratio": None,
                    "roe": None,
                    "roa": None,
                }

                # Derive book_value_per_share if we have equity and shares
                eq = report["shareholders_equity"]
                shares = _safe_val(bal, "Ordinary Shares Number", col)
                if eq is not None and shares and shares > 0:
                    report["book_value_per_share"] = eq / shares
                    report["shares_outstanding"] = int(shares)

                result.append(report)
            return result

        reports.extend(_build_reports(income_annual, balance_annual, cash_annual, "Annual"))
        reports.extend(_build_reports(income_qtr, balance_qtr, cash_qtr, "Quarterly"))

        logger.debug("Fetched %d financial reports for %s", len(reports), symbol)
        return reports
