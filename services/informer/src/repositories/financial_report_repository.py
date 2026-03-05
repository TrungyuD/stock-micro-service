"""
financial_report_repository.py — CRUD for the `financial_reports` table.
Column names match 01-schema.sql exactly.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# All income-statement / balance-sheet / cash-flow column names in schema order
_METRIC_COLS = (
    "revenue", "gross_profit", "operating_income", "net_income", "eps",
    "total_assets", "total_liabilities", "shareholders_equity", "book_value_per_share",
    "operating_cash_flow", "free_cash_flow", "capex",
    "shares_outstanding", "debt_to_equity", "current_ratio", "roe", "roa",
)


class FinancialReportRepository:
    """Data-access layer for the `financial_reports` table."""

    def __init__(self, db_pool) -> None:
        self._db = db_pool

    # ─── reads ────────────────────────────────────────────────────────────────

    def get_latest(self, stock_id: int, report_type: str) -> Optional[dict]:
        """
        Return the most recent financial report for a stock/type combination.

        Args:
            stock_id:    FK into `stocks`.
            report_type: 'Annual' or 'Quarterly'.
        """
        return self._db.execute(
            """
            SELECT *
              FROM financial_reports
             WHERE stock_id = %s AND report_type = %s
             ORDER BY report_date DESC
             LIMIT 1
            """,
            (stock_id, report_type),
            fetch="one",
        )

    def get_history(
        self,
        stock_id: int,
        report_type: str,
        years_back: int = 5,
    ) -> list[dict]:
        """
        Return financial reports going back `years_back` years.

        Args:
            stock_id:    FK into `stocks`.
            report_type: 'Annual' or 'Quarterly'.
            years_back:  How many years of history to fetch.

        Returns:
            List of report dicts ordered by report_date DESC.
        """
        return self._db.execute(
            """
            SELECT *
              FROM financial_reports
             WHERE stock_id = %s
               AND report_type = %s
               AND report_date >= (NOW() - (%s || ' years')::interval)::date
             ORDER BY report_date DESC
            """,
            (stock_id, report_type, str(years_back)),
            fetch="all",
        ) or []

    # ─── writes ───────────────────────────────────────────────────────────────

    def upsert(self, stock_id: int, report_data: dict) -> int:
        """
        Insert or update a financial report row.

        Args:
            stock_id:    FK into `stocks`.
            report_data: Dict with keys matching `financial_reports` columns.

        Returns:
            The report id (int).
        """
        metrics = tuple(report_data.get(col) for col in _METRIC_COLS)

        row = self._db.execute(
            f"""
            INSERT INTO financial_reports
                (stock_id, report_date, report_type,
                 {', '.join(_METRIC_COLS)},
                 updated_at)
            VALUES (%s, %s, %s,
                    {', '.join(['%s'] * len(_METRIC_COLS))},
                    NOW())
            ON CONFLICT (stock_id, report_date, report_type) DO UPDATE SET
                {', '.join(f'{c} = EXCLUDED.{c}' for c in _METRIC_COLS)},
                updated_at = NOW()
            RETURNING id
            """,
            (stock_id, report_data["report_date"], report_data["report_type"]) + metrics,
            fetch="one",
        )
        report_id = row["id"]
        logger.debug(
            "Upserted financial_report stock_id=%s type=%s date=%s → id=%s",
            stock_id,
            report_data.get("report_type"),
            report_data.get("report_date"),
            report_id,
        )
        return report_id
