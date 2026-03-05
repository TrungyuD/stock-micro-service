"""
data_collection_scheduler.py — APScheduler cron jobs for automated stock data collection.
Runs inside the Informer service process (BackgroundScheduler daemon threads).
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class DataCollectionScheduler:
    """
    Manages two recurring jobs:
      - daily_ohlcv:   Runs Mon-Fri at market close (configurable hour/minute EST)
                       to fetch the most-recent 5 trading days for all active stocks.
      - weekly_deep:   Runs Fridays at 18:00 EST to refresh metadata + financials.
    """

    def __init__(
        self,
        hybrid_provider,
        stock_repo,
        ohlcv_repo,
        financial_repo,
        settings,
    ) -> None:
        self._provider = hybrid_provider
        self._stock_repo = stock_repo
        self._ohlcv_repo = ohlcv_repo
        self._financial_repo = financial_repo
        self._settings = settings
        self._scheduler = BackgroundScheduler(timezone="US/Eastern")

    def start(self) -> None:
        """Register jobs and start the background scheduler."""
        # Daily OHLCV update at market close
        self._scheduler.add_job(
            self.collect_daily_ohlcv,
            CronTrigger(
                day_of_week="mon-fri",
                hour=self._settings.collection_hour,
                minute=self._settings.collection_minute,
                timezone="US/Eastern",
            ),
            id="daily_ohlcv",
            replace_existing=True,
            misfire_grace_time=3600,  # tolerate up to 1h late start
        )

        # Weekly deep refresh (metadata + financials) every Friday evening
        self._scheduler.add_job(
            self.collect_weekly_deep,
            CronTrigger(day_of_week="fri", hour=18, timezone="US/Eastern"),
            id="weekly_deep",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        self._scheduler.start()
        logger.info(
            "Scheduler started — daily_ohlcv @ %02d:%02d EST, weekly_deep @ Fri 18:00 EST",
            self._settings.collection_hour,
            self._settings.collection_minute,
        )

    def collect_daily_ohlcv(self) -> None:
        """
        Fetch the last 5 trading days of OHLCV for every active stock.
        The 5-day window covers weekends and public holidays gracefully.
        """
        from datetime import datetime, timedelta, timezone
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")

        stocks = self._stock_repo.get_all_active()
        logger.info("collect_daily_ohlcv — %d active stocks, window %s→%s", len(stocks), start_date, end_date)

        success, failed = 0, 0
        for stock in stocks:
            try:
                df = self._provider.get_historical_ohlcv(
                    stock["symbol"], start_date, end_date
                )
                if not df.empty:
                    candles = df.to_dict("records")
                    self._ohlcv_repo.bulk_upsert(stock["id"], candles)
                success += 1
            except Exception as exc:
                logger.error("collect_daily_ohlcv failed for %s: %s", stock["symbol"], exc)
                failed += 1

        logger.info("collect_daily_ohlcv complete — success=%d failed=%d", success, failed)

    def collect_weekly_deep(self) -> None:
        """
        Full metadata and financial-report refresh for every active stock.
        Runs on Fridays so fresh fundamentals are available for weekend analysis.
        """
        stocks = self._stock_repo.get_all_active()
        logger.info("collect_weekly_deep — %d active stocks", len(stocks))

        success, failed = 0, 0
        for stock in stocks:
            try:
                # Refresh metadata
                metadata = self._provider.get_stock_metadata(stock["symbol"])
                self._stock_repo.upsert(metadata)

                # Refresh financial reports
                reports = self._provider.get_financial_reports(stock["symbol"])
                for report in reports:
                    self._financial_repo.upsert(stock["id"], report)

                success += 1
            except Exception as exc:
                logger.error("collect_weekly_deep failed for %s: %s", stock["symbol"], exc)
                failed += 1

        logger.info("collect_weekly_deep complete — success=%d failed=%d", success, failed)

    def stop(self) -> None:
        """Gracefully shut down the scheduler, waiting for running jobs to finish."""
        self._scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")
