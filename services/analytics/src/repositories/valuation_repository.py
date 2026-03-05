"""
valuation-repository.py — Read/write access to the `valuation_metrics` table.
Stores pre-computed fundamental valuation ratios per stock.
"""
import logging

from database import DatabasePool

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
                data.get("trailing_pe"),
                data.get("forward_pe"),
                data.get("peg_ratio"),
                data.get("price_to_book"),
                data.get("price_to_sales"),
                data.get("ev_to_ebitda"),
                data.get("dividend_yield"),
                data.get("payout_ratio"),
                data.get("valuation_signal"),
                data.get("valuation_score"),
            ),
        )
        logger.debug("Upserted valuation_metrics for stock_id=%s at %s", stock_id, data["calculated_at"])
