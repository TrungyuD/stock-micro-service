"""
compute_helpers.py — Private compute/persist helpers used by AnalyticsHandler.
Extracted here so analytics_handler.py stays under 200 lines.
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def is_fresh_today(ts: Any) -> bool:
    """Return True if the timestamp is from today (UTC)."""
    if ts is None:
        return False
    today = datetime.now(timezone.utc).date()
    try:
        if hasattr(ts, "date"):
            return ts.date() == today
        return str(ts)[:10] == str(today)
    except Exception:
        return False


class ComputeService:
    """
    Encapsulates get-or-compute + persist logic for technicals and valuation.
    Keeps AnalyticsHandler slim — handler methods delegate here.
    """

    def __init__(self, stock_repo, indicator_repo, valuation_repo, tech_calc, val_calc):
        self._stock_repo = stock_repo
        self._ind_repo = indicator_repo
        self._val_repo = valuation_repo
        self._tech_calc = tech_calc
        self._val_calc = val_calc

    # ── Technicals ────────────────────────────────────────────────────────────

    def get_or_compute_technicals(self, stock: dict) -> dict | None:
        """Return cached indicators row; recompute if stale or missing."""
        cached = self._ind_repo.get_latest(stock["id"])
        if cached and is_fresh_today(cached.get("time")):
            return cached
        return self.compute_and_persist_technicals(stock)

    def compute_and_persist_technicals(self, stock: dict) -> dict | None:
        bars = self._stock_repo.get_ohlcv_series(stock["id"], limit=300)
        if len(bars) < 20:
            return None
        result = self._tech_calc.compute(bars)
        result["time"] = datetime.now(timezone.utc)
        self._ind_repo.upsert(stock["id"], result)
        return result

    def resolve_signals(self, ind: dict, current_price: float) -> dict:
        """
        Return signals dict for an indicator row.
        Fresh compute results carry _signals; cached DB rows do not —
        recompute from stored numeric values via compute_signals().
        """
        if "_signals" in ind:
            return ind["_signals"]
        return self._tech_calc.compute_signals(ind, current_price)

    # ── Valuation ─────────────────────────────────────────────────────────────

    def get_or_compute_valuation(self, stock: dict) -> dict | None:
        """Return cached valuation row; recompute if stale or missing."""
        cached = self._val_repo.get_latest(stock["id"])
        if cached and is_fresh_today(cached.get("calculated_at")):
            return cached
        return self.compute_and_persist_valuation(stock)

    def compute_and_persist_valuation(self, stock: dict) -> dict | None:
        current_price = self._stock_repo.get_latest_close(stock["id"])
        if not current_price:
            return None
        report = self._stock_repo.get_latest_annual_report(stock["id"])
        eps_hist = self._stock_repo.get_eps_history(stock["id"])
        rev_hist = self._stock_repo.get_revenue_history(stock["id"])
        result = self._val_calc.compute(current_price, report or {}, eps_hist, rev_hist)
        result["calculated_at"] = datetime.now(timezone.utc)
        self._val_repo.upsert(stock["id"], result)
        return result

    def run_calculation_job(self, symbols: list[str], calc_type: str) -> None:
        """Background worker: recalculate indicators/valuation for each symbol."""
        success = failed = 0
        for sym in symbols:
            try:
                stock = self._stock_repo.get_stock_by_symbol(sym)
                if not stock:
                    failed += 1
                    continue
                if calc_type in ("technicals", "all"):
                    self.compute_and_persist_technicals(stock)
                if calc_type in ("valuation", "all"):
                    self.compute_and_persist_valuation(stock)
                success += 1
            except Exception as exc:
                logger.error("calc-job failed for %s: %s", sym, exc)
                failed += 1
        logger.info("TriggerCalculation done — success=%d failed=%d", success, failed)
