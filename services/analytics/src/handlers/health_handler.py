"""
health_handler.py — Shared HealthService gRPC handler for Analytics.
Implements the Check RPC from generated.health_pb2_grpc.
"""
import logging
from datetime import datetime, timezone

import grpc

from generated import health_pb2, health_pb2_grpc

logger = logging.getLogger(__name__)

_VERSION = "1.0.0"
_START_TIME = datetime.now(timezone.utc)


class HealthHandler(health_pb2_grpc.HealthServiceServicer):
    """Implements HealthService.Check — reports DB connectivity and uptime."""

    def __init__(self, db_pool=None) -> None:
        self._db_pool = db_pool

    def Check(self, request, context):
        """Standard health check. Returns SERVING when DB is reachable."""
        db_ok = False
        try:
            if self._db_pool:
                db_ok = self._db_pool.health_check()
        except Exception as exc:
            logger.warning("HealthHandler: DB probe failed: %s", exc)
        status = "SERVING" if db_ok else "NOT_SERVING"
        uptime = f"{int((datetime.now(timezone.utc) - _START_TIME).total_seconds())}s"
        return health_pb2.HealthCheckResponse(
            status=status, version=_VERSION, uptime=uptime
        )
