"""
valuation_repository.py — Read/write access to the `valuation_metrics` table.
Stores pre-computed fundamental valuation ratios per stock.
"""
import logging

from database import DatabasePool
from utils.numeric_helpers import to_native

logger = logging.getLogger(__name__)


class ValuationRepository:
    """CRUD operations for the `valuation_metrics` table."""

    def __init__(self, db: DatabasePool) -> None:
        self._db = db

    def get_latest(self, stock_id: int) -> dict | None:
        """Return the most-recent valuation_metrics row for a stock."""
        return self._db.execute(
            "SELECT * FROM valuation_metrics "
            "WHERE stock_id = %s ORDER BY calculated_at DESC LIMIT 1",
            (stock_id,),
            fetch="one",
        )

    def get_all_latest(self) -> list[dict]:
        """
        Return the most-recent valuation row for every stock (one row per stock_id).
        Used by ScreenStocks to scan all stocks efficiently.
        """
        return self._db.execute(
            """
            SELECT DISTINCT ON (vm.stock_id)
                vm.*, s.symbol, s.name, s.sector
            FROM valuation_metrics vm
            JOIN stocks s ON s.id = vm.stock_id
            WHERE s.is_active = TRUE
            ORDER BY vm.stock_id, vm.calculated_at DESC
            """,
            fetch="all",
        ) or []

    def get_screening_data(self) -> list[dict]:
        """
        Single batch query returning valuation + latest close + latest indicators
        for all active stocks. Replaces 3 separate per-stock queries in ScreenStocks.

        Uses LATERAL joins for efficient "latest row per stock" pattern.
        Returns one row per stock with prefixed columns:
          - vm.* columns (valuation metrics)
          - s.symbol, s.name, s.sector (stock info)
          - latest_close (from ohlcv)
          - ind_* columns (from indicators)
        """
        return self._db.execute(
            """
            SELECT DISTINCT ON (vm.stock_id)
                vm.*,
                s.symbol, s.name, s.sector,
                ohlcv_lat.close AS latest_close,
                ind_lat.rsi_14 AS ind_rsi_14,
                ind_lat.sma_20 AS ind_sma_20,
                ind_lat.sma_50 AS ind_sma_50,
                ind_lat.sma_200 AS ind_sma_200,
                ind_lat.ema_20 AS ind_ema_20,
                ind_lat.ema_50 AS ind_ema_50,
                ind_lat.macd_line AS ind_macd_line,
                ind_lat.macd_signal AS ind_macd_signal,
                ind_lat.macd_histogram AS ind_macd_histogram,
                ind_lat.bb_upper AS ind_bb_upper,
                ind_lat.bb_middle AS ind_bb_middle,
                ind_lat.bb_lower AS ind_bb_lower
            FROM valuation_metrics vm
            JOIN stocks s ON s.id = vm.stock_id AND s.is_active = TRUE
            LEFT JOIN LATERAL (
                SELECT close FROM ohlcv
                WHERE stock_id = vm.stock_id
                ORDER BY time DESC LIMIT 1
            ) ohlcv_lat ON true
            LEFT JOIN LATERAL (
                SELECT rsi_14, sma_20, sma_50, sma_200, ema_20, ema_50,
                       macd_line, macd_signal, macd_histogram,
                       bb_upper, bb_middle, bb_lower
                FROM indicators
                WHERE stock_id = vm.stock_id
                ORDER BY time DESC LIMIT 1
            ) ind_lat ON true
            ORDER BY vm.stock_id, vm.calculated_at DESC
            """,
            fetch="all",
        ) or []

    def upsert(self, stock_id: int, data: dict) -> None:
        """
        Insert a new valuation_metrics row.
        Uses ON CONFLICT (stock_id, calculated_at) DO UPDATE.
        """
        self._db.execute(
            """
            INSERT INTO valuation_metrics (
                stock_id, calculated_at,
                trailing_pe, forward_pe, peg_ratio,
                price_to_book, price_to_sales, ev_to_ebitda,
                dividend_yield, payout_ratio,
                valuation_signal, valuation_score
            ) VALUES (
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s
            )
            ON CONFLICT (stock_id, calculated_at) DO UPDATE SET
                trailing_pe     = EXCLUDED.trailing_pe,
                forward_pe      = EXCLUDED.forward_pe,
                peg_ratio       = EXCLUDED.peg_ratio,
                price_to_book   = EXCLUDED.price_to_book,
                price_to_sales  = EXCLUDED.price_to_sales,
                ev_to_ebitda    = EXCLUDED.ev_to_ebitda,
                dividend_yield  = EXCLUDED.dividend_yield,
                payout_ratio    = EXCLUDED.payout_ratio,
                valuation_signal = EXCLUDED.valuation_signal,
                valuation_score  = EXCLUDED.valuation_score
            """,
            (
                stock_id,
                data["calculated_at"],
                to_native(data.get("trailing_pe")),
                to_native(data.get("forward_pe")),
                to_native(data.get("peg_ratio")),
                to_native(data.get("price_to_book")),
                to_native(data.get("price_to_sales")),
                to_native(data.get("ev_to_ebitda")),
                to_native(data.get("dividend_yield")),
                to_native(data.get("payout_ratio")),
                data.get("valuation_signal"),
                to_native(data.get("valuation_score")),
            ),
        )
        logger.debug("Upserted valuation_metrics for stock_id=%s at %s", stock_id, data["calculated_at"])
