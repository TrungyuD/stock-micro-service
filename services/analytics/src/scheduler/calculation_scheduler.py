"""
calculation-scheduler.py — APScheduler cron job that recalculates all technical
indicators and valuation metrics after US market close (Mon-Fri).
Runs inside the Analytics service process as a BackgroundScheduler daemon thread.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class CalculationScheduler:
    """
    Schedules one daily job:
      - after_market_close: Mon-Fri at 17:00 EST — recompute all technicals + valuations
        for every active stock so RPCs always return fresh cached results.
    """

    def __init__(
        self,
        stock_data_repo,
        indicator_repo,
        valuation_repo,
        tech_calc,
        val_calc,
        settings,
    ) -> None:
        self._stock_repo = stock_data_repo
        self._ind_repo = indicator_repo
        self._val_repo = valuation_repo
        self._tech_calc = tech_calc
        self._val_calc = val_calc
        self._settings = settings
        self._scheduler = BackgroundScheduler(timezone="US/Eastern")

    def start(self) -> None:
        """Register jobs and start the background scheduler."""
        self._scheduler.add_job(
            self.recalculate_all,
            CronTrigger(
                day_of_week="mon-fri",
                hour=self._settings.calc_hour,
                minute=self._settings.calc_minute,
                timezone="US/Eastern",
            ),
            id="after_market_close",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        self._scheduler.start()
        logger.info(
            "CalculationScheduler started — daily recalc @ %02d:%02d EST (Mon-Fri)",
            self._settings.calc_hour,
            self._settings.calc_minute,
        )

    def recalculate_all(self) -> None:
        """
        Fetch all active stocks and recompute both technical indicators and
        valuation metrics, persisting results to the DB.
        """
        from datetime import datetime, timezone

        stocks = self._stock_repo.get_all_active_stocks()
        logger.info("recalculate_all — %d active stocks", len(stocks))
        success = failed = 0

        for stock in stocks:
            try:
                self._recalculate_technicals(stock)
                self._recalculate_valuation(stock)
                success += 1
            except Exception as exc:
                logger.error("recalculate_all failed for %s: %s", stock.get("symbol"), exc)
                failed += 1

        logger.info("recalculate_all complete — success=%d failed=%d", success, failed)

    def _recalculate_technicals(self, stock: dict) -> None:
        """Recompute and persist technical indicators for one stock."""
        from datetime import datetime, timezone

        bars = self._stock_repo.get_ohlcv_series(stock["id"], limit=300)
        if len(bars) < 20:
            logger.debug("Skip technicals for %s — only %d bars", stock["symbol"], len(bars))
            return

        result = self._tech_calc.compute(bars)
        result["time"] = datetime.now(timezone.utc)
        self._ind_repo.upsert(stock["id"], result)

    def _recalculate_valuation(self, stock: dict) -> None:
        """Recompute and persist valuation metrics for one stock."""
        from datetime import datetime, timezone

        current_price = self._stock_repo.get_latest_close(stock["id"])
        if not current_price:
            logger.debug("Skip valuation for %s — no price data", stock["symbol"])
            return

        report = self._stock_repo.get_latest_annual_report(stock["id"])
        eps_hist = self._stock_repo.get_eps_history(stock["id"])
        rev_hist = self._stock_repo.get_revenue_history(stock["id"])

        result = self._val_calc.compute(current_price, report or {}, eps_hist, rev_hist)
        result["calculated_at"] = datetime.now(timezone.utc)
        self._val_repo.upsert(stock["id"], result)

    def stop(self) -> None:
        """Gracefully shut down the scheduler, waiting for running jobs."""
        self._scheduler.shutdown(wait=True)
        logger.info("CalculationScheduler stopped")
