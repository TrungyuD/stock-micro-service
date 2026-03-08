"""
calculation_scheduler.py — APScheduler cron job that recalculates all technical
indicators and valuation metrics after US market close (Mon-Fri).
Delegates computation to ComputeService to avoid logic duplication.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from handlers.compute_helpers import ComputeService
from repositories.indicator_repository import IndicatorRepository
from repositories.stock_data_repository import StockDataRepository
from repositories.valuation_repository import ValuationRepository

logger = logging.getLogger(__name__)


class CalculationScheduler:
    """
    Schedules one daily job:
      - after_market_close: Mon-Fri at 17:00 EST — recompute all technicals + valuations
        for every active stock so RPCs always return fresh cached results.
    """

    def __init__(
        self,
        stock_data_repo: StockDataRepository,
        indicator_repo: IndicatorRepository,
        valuation_repo: ValuationRepository,
        tech_calc,
        val_calc,
        settings,
    ) -> None:
        self._stock_repo = stock_data_repo
        # Build a ComputeService to reuse compute+persist logic (DRY)
        self._compute_svc = ComputeService(
            stock_data_repo, indicator_repo, valuation_repo, tech_calc, val_calc
        )
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
        valuation metrics via ComputeService, persisting results to the DB.
        """
        stocks = self._stock_repo.get_all_active_stocks()
        logger.info("recalculate_all — %d active stocks", len(stocks))
        symbols = [s.get("symbol", "") for s in stocks]
        # Delegate to ComputeService.run_calculation_job which handles
        # per-symbol error isolation and logging
        self._compute_svc.run_calculation_job(symbols, "all")

    def stop(self) -> None:
        """Gracefully shut down the scheduler, waiting for running jobs."""
        self._scheduler.shutdown(wait=True)
        logger.info("CalculationScheduler stopped")
