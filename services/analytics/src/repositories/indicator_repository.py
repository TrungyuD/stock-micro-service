"""
indicator-repository.py — Read/write access to the `indicators` table.
Stores pre-computed technical indicators so they are not recalculated on every RPC call.
"""
import logging
from typing import Any

import numpy as np

from database import DatabasePool

logger = logging.getLogger(__name__)


def _to_native(v: Any) -> Any:
    """Convert numpy scalars to native Python types for psycopg2 compatibility."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


class IndicatorRepository:
    """CRUD operations for the `indicators` (technical indicators) table."""

    def __init__(self, db: DatabasePool) -> None:
        self._db = db

    def get_latest(self, stock_id: int) -> dict | None:
        """Return the most-recent indicators row for a stock."""
        return self._db.execute(
            "SELECT * FROM indicators WHERE stock_id = %s ORDER BY time DESC LIMIT 1",
            (stock_id,),
            fetch="one",
        )

    def upsert(self, stock_id: int, data: dict) -> None:
        """
        Insert or update indicators for a specific (stock_id, time) pair.
        Uses ON CONFLICT (stock_id, time) DO UPDATE to handle re-runs.
        """
        self._db.execute(
            """
            INSERT INTO indicators (
                stock_id, time,
                rsi_14,
                sma_20, sma_50, sma_200,
                ema_20, ema_50,
                macd_line, macd_signal, macd_histogram,
                bb_upper, bb_middle, bb_lower
            ) VALUES (
                %s, %s,
                %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (stock_id, time) DO UPDATE SET
                rsi_14          = EXCLUDED.rsi_14,
                sma_20          = EXCLUDED.sma_20,
                sma_50          = EXCLUDED.sma_50,
                sma_200         = EXCLUDED.sma_200,
                ema_20          = EXCLUDED.ema_20,
                ema_50          = EXCLUDED.ema_50,
                macd_line       = EXCLUDED.macd_line,
                macd_signal     = EXCLUDED.macd_signal,
                macd_histogram  = EXCLUDED.macd_histogram,
                bb_upper        = EXCLUDED.bb_upper,
                bb_middle       = EXCLUDED.bb_middle,
                bb_lower        = EXCLUDED.bb_lower
            """,
            (
                stock_id,
                data["time"],
                _to_native(data.get("rsi_14")),
                _to_native(data.get("sma_20")),
                _to_native(data.get("sma_50")),
                _to_native(data.get("sma_200")),
                _to_native(data.get("ema_20")),
                _to_native(data.get("ema_50")),
                _to_native(data.get("macd_line")),
                _to_native(data.get("macd_signal")),
                _to_native(data.get("macd_histogram")),
                _to_native(data.get("bb_upper")),
                _to_native(data.get("bb_middle")),
                _to_native(data.get("bb_lower")),
            ),
        )
        logger.debug("Upserted indicators for stock_id=%s at %s", stock_id, data["time"])
