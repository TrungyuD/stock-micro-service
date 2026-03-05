"""
server.py — Analytics gRPC server entry point.
Wires up all dependencies and starts the server with graceful shutdown.
"""
import logging
import os
import signal
import sys
from concurrent import futures

# Ensure src/ is on sys.path for absolute imports regardless of launch directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import grpc

from calculators.technical_calculator import TechnicalCalculator
from calculators.valuation_calculator import ValuationCalculator
from config import Settings
from database import DatabasePool
from handlers.analytics_handler import AnalyticsHandler
from repositories.indicator_repository import IndicatorRepository
from repositories.stock_data_repository import StockDataRepository
from repositories.valuation_repository import ValuationRepository
from scheduler.calculation_scheduler import CalculationScheduler
from generated import analytics_pb2_grpc

# Configure structured logging before importing other local modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("analytics.server")


def serve() -> None:
    """Bootstrap all dependencies and start the gRPC server."""
    settings = Settings()

    # Override log level from config
    logging.getLogger().setLevel(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    )

    # ── Database ──────────────────────────────────────────────────────────────
    db_pool = DatabasePool(settings)
    db_pool.initialize()

    # ── Repositories ──────────────────────────────────────────────────────────
    stock_data_repo = StockDataRepository(db_pool)
    indicator_repo = IndicatorRepository(db_pool)
    valuation_repo = ValuationRepository(db_pool)

    # ── Calculators ───────────────────────────────────────────────────────────
    tech_calc = TechnicalCalculator()
    val_calc = ValuationCalculator()

    # ── Handler ───────────────────────────────────────────────────────────────
    handler = AnalyticsHandler(stock_data_repo, indicator_repo, valuation_repo)

    # ── gRPC server ───────────────────────────────────────────────────────────
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.grpc_max_workers),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )
    analytics_pb2_grpc.add_AnalyticsServiceServicer_to_server(handler, server)
    server.add_insecure_port(settings.grpc_address)
    server.start()
    logger.info("Analytics gRPC server listening on %s", settings.grpc_address)

    # ── Scheduler ─────────────────────────────────────────────────────────────
    scheduler: CalculationScheduler | None = None
    if settings.enable_scheduler:
        scheduler = CalculationScheduler(
            stock_data_repo, indicator_repo, valuation_repo,
            tech_calc, val_calc, settings,
        )
        scheduler.start()
        logger.info("Calculation scheduler started")

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    def _shutdown(signum, frame) -> None:
        logger.info("Shutting down Analytics server (signal %s)…", signum)
        if scheduler:
            scheduler.stop()
        server.stop(grace=10)
        db_pool.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Analytics service ready")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
