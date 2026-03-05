"""
database.py — PostgreSQL connection pool for the Analytics service.
Uses psycopg2 ThreadedConnectionPool with a context manager for safe checkout/return.
Matches the pattern used by the Informer service for consistency.
"""
import logging
from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)


class DatabasePool:
    """
    Wraps psycopg2 ThreadedConnectionPool.
    Provides a context manager for safe connection checkout/return and
    a helper for executing parameterized queries.
    """

    def __init__(self, settings) -> None:
        self._settings = settings
        self._pool: pool.ThreadedConnectionPool | None = None

    def initialize(self) -> None:
        """Create the connection pool and verify DB connectivity."""
        self._pool = pool.ThreadedConnectionPool(
            minconn=self._settings.db_pool_min,
            maxconn=self._settings.db_pool_max,
            **self._settings.db_dsn,
        )
        # Health-check: fetch a connection and immediately return it
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        finally:
            self._pool.putconn(conn)
        logger.info(
            "DB pool ready — %s@%s:%s/%s",
            self._settings.db_user,
            self._settings.db_host,
            self._settings.db_port,
            self._settings.db_name,
        )

    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("DB pool closed")

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Context manager that checks out one connection from the pool.
        Commits on success, rolls back on exception, always returns connection.
        """
        assert self._pool is not None, "DatabasePool not initialized"
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def execute(
        self,
        sql: str,
        params: tuple = (),
        fetch: str = "none",
    ) -> Any:
        """
        Execute a single parameterized SQL statement.

        Args:
            sql:    Parameterized SQL string (use %s placeholders).
            params: Tuple of bind values.
            fetch:  'none' | 'one' | 'all' — controls what is returned.

        Returns:
            None | dict | list[dict] depending on `fetch`.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetch == "one":
                    row = cur.fetchone()
                    if row is None:
                        return None
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, row))
                if fetch == "all":
                    rows = cur.fetchall()
                    cols = [desc[0] for desc in cur.description]
                    return [dict(zip(cols, row)) for row in rows]
                return None
