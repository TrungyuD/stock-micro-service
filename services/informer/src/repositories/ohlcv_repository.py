"""
ohlcv_repository.py — Read/write operations for the TimescaleDB `ohlcv` hypertable.
Uses ON CONFLICT DO NOTHING for idempotent bulk inserts.
"""
import logging
from datetime import date, datetime
from typing import Optional

import psycopg2.extras

logger = logging.getLogger(__name__)

# Maximum rows per INSERT batch to avoid overly large statements
_BATCH_SIZE = 500


class OHLCVRepository:
    """Data-access layer for the `ohlcv` time-series hypertable."""

    def __init__(self, db_pool) -> None:
        self._db = db_pool

    # ─── reads ────────────────────────────────────────────────────────────────

    def get_latest(self, stock_id: int) -> Optional[dict]:
        """Return the most recent OHLCV row for a stock, or None."""
        return self._db.execute(
            """
            SELECT time, stock_id, open, high, low, close, volume, adjusted_close
              FROM ohlcv
             WHERE stock_id = %s
             ORDER BY time DESC
             LIMIT 1
            """,
            (stock_id,),
            fetch="one",
        )

    def get_history(
        self,
        stock_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 0,
    ) -> list[dict]:
        """
        Return OHLCV rows for a stock within an optional date range.

        Args:
            stock_id:   FK into `stocks`.
            start_date: ISO date string 'YYYY-MM-DD' (inclusive), or None.
            end_date:   ISO date string 'YYYY-MM-DD' (inclusive), or None.
            limit:      Max rows to return; 0 = unlimited.

        Returns:
            List of dicts ordered by time ASC.
        """
        conditions = ["stock_id = %s"]
        params: list = [stock_id]

        if start_date:
            conditions.append("time >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("time <= %s")
            params.append(end_date)

        where = " AND ".join(conditions)
        limit_clause = f"LIMIT {int(limit)}" if limit > 0 else ""

        return self._db.execute(
            f"""
            SELECT time, stock_id, open, high, low, close, volume, adjusted_close
              FROM ohlcv
             WHERE {where}
             ORDER BY time ASC
             {limit_clause}
            """,
            tuple(params),
            fetch="all",
        ) or []

    # ─── writes ───────────────────────────────────────────────────────────────

    def bulk_upsert(self, stock_id: int, candles: list[dict]) -> int:
        """
        Insert OHLCV rows in batches; silently skip duplicates via ON CONFLICT.

        Args:
            stock_id: FK into `stocks`.
            candles:  List of dicts with keys: time, open, high, low, close,
                      volume, adjusted_close (optional).

        Returns:
            Number of rows accepted (before deduplication at DB level).
        """
        if not candles:
            return 0

        inserted = 0
        # Process in fixed-size batches to keep memory bounded
        for batch_start in range(0, len(candles), _BATCH_SIZE):
            batch = candles[batch_start: batch_start + _BATCH_SIZE]
            rows = [
                (
                    c["time"],
                    stock_id,
                    float(c["open"]),
                    float(c["high"]),
                    float(c["low"]),
                    float(c["close"]),
                    int(c["volume"]),
                    float(c["adjusted_close"]) if c.get("adjusted_close") is not None else None,
                )
                for c in batch
            ]

            with self._db.get_connection() as conn:
                with conn.cursor() as cur:
                    psycopg2.extras.execute_values(
                        cur,
                        """
                        INSERT INTO ohlcv
                            (time, stock_id, open, high, low, close, volume, adjusted_close)
                        VALUES %s
                        ON CONFLICT (stock_id, time) DO NOTHING
                        """,
                        rows,
                        template="(%s, %s, %s, %s, %s, %s, %s, %s)",
                    )
            inserted += len(batch)

        logger.debug(
            "bulk_upsert stock_id=%s: %d candles submitted in %d batches",
            stock_id,
            len(candles),
            (len(candles) + _BATCH_SIZE - 1) // _BATCH_SIZE,
        )
        return inserted
