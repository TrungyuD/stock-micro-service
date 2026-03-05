#!/usr/bin/env python3
"""
backfill-historical-data.py — One-time script to seed 5 years of OHLCV data
and the latest annual/quarterly financial reports for a list of seed symbols.

Usage (from repo root):
    cd stock-micro-service
    PYTHONPATH=services/informer/src python scripts/backfill-historical-data.py

Environment variables (or .env file in services/informer/):
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    ALPHA_VANTAGE_KEY  (optional)

Rate: ~1 req/sec (yfinance) → 20 symbols × 2 calls ≈ 40 seconds minimum.
"""
import logging
import os
import sys
from datetime import datetime, timedelta

# Allow running from repo root with PYTHONPATH=services/informer/src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "informer", "src"))

# Load .env from the informer service directory if present
_env_file = os.path.join(os.path.dirname(__file__), "..", "services", "informer", ".env")
if os.path.exists(_env_file):
    from dotenv import load_dotenv
    load_dotenv(_env_file)

from config import Settings
from database import DatabasePool
from providers.yfinance_provider import YFinanceProvider
from providers.fallback_provider import AlphaVantageProvider
from repositories.stock_repository import StockRepository
from repositories.ohlcv_repository import OHLCVRepository
from repositories.financial_report_repository import FinancialReportRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backfill")

# ── Seed symbols ──────────────────────────────────────────────────────────────
# Extend this list or replace with a DB query for all active stocks
SEED_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK.B", "JPM", "JNJ",
    "V", "PG", "UNH", "HD", "MA",
    "XOM", "CVX", "LLY", "ABBV", "MRK",
]

# ── Date range: 5 years back from today ───────────────────────────────────────
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")
START_DATE = (datetime.utcnow() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")


def backfill() -> None:
    settings = Settings()
    db_pool = DatabasePool(settings)
    db_pool.initialize()

    stock_repo = StockRepository(db_pool)
    ohlcv_repo = OHLCVRepository(db_pool)
    financial_repo = FinancialReportRepository(db_pool)

    yf_provider = YFinanceProvider()
    av_provider = AlphaVantageProvider(api_key=settings.alpha_vantage_key)

    logger.info(
        "Backfill started — %d symbols | %s → %s",
        len(SEED_SYMBOLS), START_DATE, END_DATE,
    )

    ohlcv_ok, ohlcv_fail = 0, 0
    fin_ok, fin_fail = 0, 0

    for symbol in SEED_SYMBOLS:
        logger.info("── %s ──", symbol)

        # 1. Metadata upsert
        try:
            metadata = yf_provider.get_stock_metadata(symbol)
            stock_id = stock_repo.upsert(metadata)
            logger.info("  metadata OK (id=%s)", stock_id)
        except Exception as exc:
            logger.error("  metadata FAILED: %s", exc)
            # Try to resolve existing stock_id for OHLCV/financials
            row = stock_repo.get_by_symbol(symbol)
            stock_id = row["id"] if row else None

        if not stock_id:
            logger.warning("  skipping OHLCV/financials — no stock_id for %s", symbol)
            ohlcv_fail += 1
            fin_fail += 1
            continue

        # 2. Historical OHLCV (5 years)
        try:
            df = yf_provider.get_historical_ohlcv(symbol, START_DATE, END_DATE)
            if not df.empty:
                count = ohlcv_repo.bulk_upsert(stock_id, df.to_dict("records"))
                logger.info("  OHLCV OK — %d bars submitted", count)
                ohlcv_ok += 1
            else:
                logger.warning("  OHLCV empty from yfinance for %s", symbol)
                ohlcv_fail += 1
        except Exception as exc:
            logger.error("  OHLCV FAILED: %s", exc)
            ohlcv_fail += 1

        # 3. Financial reports (annual + quarterly)
        try:
            reports = yf_provider.get_financial_reports(symbol)
            for report in reports:
                financial_repo.upsert(stock_id, report)
            logger.info("  financials OK — %d reports", len(reports))
            fin_ok += 1
        except Exception as exc:
            logger.error("  financials FAILED: %s — trying Alpha Vantage", exc)
            if settings.alpha_vantage_key:
                try:
                    reports = av_provider.get_financial_reports(symbol)
                    for report in reports:
                        financial_repo.upsert(stock_id, report)
                    logger.info("  financials OK via AV fallback — %d reports", len(reports))
                    fin_ok += 1
                except Exception as av_exc:
                    logger.error("  financials AV fallback FAILED: %s", av_exc)
                    fin_fail += 1
            else:
                fin_fail += 1

    db_pool.close()
    logger.info(
        "Backfill complete — OHLCV ok=%d fail=%d | financials ok=%d fail=%d",
        ohlcv_ok, ohlcv_fail, fin_ok, fin_fail,
    )


if __name__ == "__main__":
    backfill()
