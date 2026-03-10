"""
server.py — Informer gRPC server entry point.
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

from config import Settings
from database import DatabasePool
from handlers.informer_handler import InformerHandler
from providers.hybrid_provider import HybridProvider
from repositories.stock_repository import StockRepository
from repositories.ohlcv_repository import OHLCVRepository
from repositories.financial_report_repository import FinancialReportRepository
from scheduler.data_collection_scheduler import DataCollectionScheduler
from generated import informer_pb2_grpc
from utils.retry import retry_with_backoff

# Configure structured logging before importing other local modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("informer.server")


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
    stock_repo = StockRepository(db_pool)
    ohlcv_repo = OHLCVRepository(db_pool)
    financial_repo = FinancialReportRepository(db_pool)

    # ── Providers ─────────────────────────────────────────────────────────────
    provider = HybridProvider(settings, db_pool)
    # Wire repos into provider so it can persist fetched data
    provider.stock_repo = stock_repo
    provider.ohlcv_repo = ohlcv_repo
    provider.financial_repo = financial_repo

    # ── Handler ───────────────────────────────────────────────────────────────
    handler = InformerHandler(provider, stock_repo, ohlcv_repo, financial_repo)

    # ── gRPC server ───────────────────────────────────────────────────────────
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.grpc_max_workers),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )
    informer_pb2_grpc.add_InformerServiceServicer_to_server(handler, server)
    server.add_insecure_port(settings.grpc_address)
    server.start()
    logger.info("Informer gRPC server listening on %s", settings.grpc_address)

    # ── Scheduler ─────────────────────────────────────────────────────────────
    scheduler: DataCollectionScheduler | None = None
    if settings.enable_scheduler:
        scheduler = DataCollectionScheduler(
            provider, stock_repo, ohlcv_repo, financial_repo, settings
        )
        scheduler.start()
        logger.info("Data collection scheduler started")

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    def _shutdown(signum, frame) -> None:
        logger.info("Shutting down (signal %s)…", signum)
        if scheduler:
            scheduler.stop()
        server.stop(grace=10)  # 10s grace period for in-flight RPCs
        db_pool.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Informer service ready")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
