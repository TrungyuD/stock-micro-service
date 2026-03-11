"""
health_handler.py — Shared HealthService gRPC handler.
Implements HealthServiceServicer from generated.health_pb2_grpc.
"""
import logging
from datetime import datetime, timezone

from generated import health_pb2, health_pb2_grpc

logger = logging.getLogger(__name__)

# Service version reported in health check response
_VERSION = "1.0.0"
_START_TIME = datetime.now(timezone.utc)


class HealthHandler(health_pb2_grpc.HealthServiceServicer):
    """
    Implements the Check RPC defined in health.proto.
    Probes DB connectivity and reports uptime.
    """

    def __init__(self, stock_repo) -> None:
        self._stock_repo = stock_repo

    def Check(self, request, context):
        """Return service status and DB connectivity. Lightweight SELECT 1 probe."""
        db_ok = False
        try:
            self._stock_repo._db.execute("SELECT 1", fetch="one")
            db_ok = True
        except Exception as exc:
            logger.warning("HealthCheck DB probe failed: %s", exc)

        status = "SERVING" if db_ok else "NOT_SERVING"
        uptime_secs = (datetime.now(timezone.utc) - _START_TIME).total_seconds()

        return health_pb2.HealthCheckResponse(
            status=status,
            version=_VERSION,
            uptime=f"{int(uptime_secs)}s",
        )
