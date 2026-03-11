"""
server.py — Analytics gRPC server entry point.
Wires up all dependencies and starts the server with graceful shutdown.
Registers v1 services: TechnicalAnalysis, FundamentalAnalysis, Screening, Scoring, Health.
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
from handlers.compute_helpers import ComputeService
from handlers.fundamental_handler import FundamentalHandler
from handlers.health_handler import HealthHandler
from handlers.scoring_handler import ScoringHandler
from handlers.screening_handler import ScreeningHandler
from handlers.technical_handler import TechnicalHandler
from repositories.indicator_repository import IndicatorRepository
from repositories.stock_data_repository import StockDataRepository
from repositories.valuation_repository import ValuationRepository
from scheduler.calculation_scheduler import CalculationScheduler
from utils.retry import retry_with_backoff

from generated.analyzer.v1 import (
    fundamental_pb2_grpc,
    scoring_pb2_grpc,
    screening_pb2_grpc,
    technical_pb2_grpc,
)
from generated import health_pb2_grpc

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

    @retry_with_backoff(max_retries=5, backoff_factor=2.0, exceptions=(Exception,))
    def _init_db():
        db_pool.initialize()

    _init_db()

    # ── Repositories ──────────────────────────────────────────────────────────
    stock_data_repo = StockDataRepository(db_pool)
    indicator_repo = IndicatorRepository(db_pool)
    valuation_repo = ValuationRepository(db_pool)

    # ── Calculators ───────────────────────────────────────────────────────────
    tech_calc = TechnicalCalculator()
    val_calc = ValuationCalculator()

    # ── Shared ComputeService (used by all v1 handlers) ───────────────────────
    svc = ComputeService(
        stock_data_repo, indicator_repo, valuation_repo, tech_calc, val_calc
    )

    # ── V1 handlers ───────────────────────────────────────────────────────────
    tech_handler = TechnicalHandler(stock_data_repo, svc)
    fund_handler = FundamentalHandler(stock_data_repo, svc)
    screen_handler = ScreeningHandler(stock_data_repo, valuation_repo, svc)
    score_handler = ScoringHandler(stock_data_repo, svc)
    health_handler = HealthHandler(db_pool=db_pool)

    # ── gRPC server ───────────────────────────────────────────────────────────
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.grpc_max_workers),
        options=[
            ("grpc.max_send_message_length", 10 * 1024 * 1024),
            ("grpc.max_receive_message_length", 10 * 1024 * 1024),
        ],
    )

    # Register v1 services
    technical_pb2_grpc.add_TechnicalAnalysisServiceServicer_to_server(tech_handler, server)
    fundamental_pb2_grpc.add_FundamentalAnalysisServiceServicer_to_server(fund_handler, server)
    screening_pb2_grpc.add_ScreeningServiceServicer_to_server(screen_handler, server)
    scoring_pb2_grpc.add_ScoringServiceServicer_to_server(score_handler, server)
    health_pb2_grpc.add_HealthServiceServicer_to_server(health_handler, server)

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
