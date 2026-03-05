"""
stock-data-repository.py — READ-ONLY access to stocks, ohlcv, and financial_reports tables.
Analytics service only reads data that was written by the Informer service.
"""
import logging
from typing import Any

from database import DatabasePool

logger = logging.getLogger(__name__)


class StockDataRepository:
    """
    Read-only queries against stocks, ohlcv, and financial_reports tables.
    All writes to these tables are owned by the Informer service.
    """

    def __init__(self, db: DatabasePool) -> None:
        self._db = db

    # ─── Stocks ───────────────────────────────────────────────────────────────

    def get_stock_by_symbol(self, symbol: str) -> dict | None:
        """Return the stocks row for the given symbol, or None."""
        return self._db.execute(
            "SELECT id, symbol, name, sector, industry, exchange, market_cap "
            "FROM stocks WHERE symbol = %s AND is_active = TRUE",
            (symbol,),
            fetch="one",
        )

    def get_all_active_stocks(self) -> list[dict]:
        """Return all active stocks (id, symbol, name, sector)."""
        return self._db.execute(
            "SELECT id, symbol, name, sector FROM stocks WHERE is_active = TRUE ORDER BY symbol",
            fetch="all",
        ) or []

    def get_stocks_by_sector(self, sector: str) -> list[dict]:
        """Return all active stocks in a given sector."""
        return self._db.execute(
            "SELECT id, symbol, name, sector FROM stocks "
            "WHERE is_active = TRUE AND sector = %s ORDER BY symbol",
            (sector,),
            fetch="all",
        ) or []

    # ─── OHLCV ────────────────────────────────────────────────────────────────

    def get_ohlcv_series(self, stock_id: int, limit: int = 300) -> list[dict]:
        """
        Return up to `limit` most-recent OHLCV bars for a stock, ordered oldest-first.
        300 bars is enough for SMA-200 + buffer.
        """
        rows = self._db.execute(
            "SELECT time, open, high, low, close, volume, adjusted_close "
            "FROM ohlcv WHERE stock_id = %s "
            "ORDER BY time DESC LIMIT %s",
            (stock_id, limit),
            fetch="all",
        ) or []
        # Reverse so oldest-first for rolling calculations
        return list(reversed(rows))

    def get_latest_close(self, stock_id: int) -> float | None:
        """Return the most-recent closing price for a stock."""
        row = self._db.execute(
            "SELECT close FROM ohlcv WHERE stock_id = %s ORDER BY time DESC LIMIT 1",
            (stock_id,),
            fetch="one",
        )
        if row:
            return float(row["close"])
        return None

    # ─── Financial Reports ────────────────────────────────────────────────────

    def get_latest_annual_report(self, stock_id: int) -> dict | None:
        """Return the most-recent Annual financial report."""
        return self._db.execute(
            "SELECT * FROM financial_reports "
            "WHERE stock_id = %s AND report_type = 'Annual' "
            "ORDER BY report_date DESC LIMIT 1",
            (stock_id,),
            fetch="one",
        )

    def get_eps_history(self, stock_id: int, limit: int = 5) -> list[dict]:
        """Return up to `limit` most-recent annual EPS values for PEG calculation."""
        rows = self._db.execute(
            "SELECT report_date, eps FROM financial_reports "
            "WHERE stock_id = %s AND report_type = 'Annual' AND eps IS NOT NULL "
            "ORDER BY report_date DESC LIMIT %s",
            (stock_id, limit),
            fetch="all",
        ) or []
        return rows

    def get_revenue_history(self, stock_id: int, limit: int = 4) -> list[dict]:
        """Return up to `limit` most-recent annual revenue rows (for EV/EBITDA + P/S)."""
        rows = self._db.execute(
            "SELECT report_date, revenue, operating_income, shares_outstanding "
            "FROM financial_reports "
            "WHERE stock_id = %s AND report_type = 'Annual' "
            "ORDER BY report_date DESC LIMIT %s",
            (stock_id, limit),
            fetch="all",
        ) or []
        return rows
