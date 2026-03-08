"""
config.py — Analytics service configuration loaded from environment variables.
Uses pydantic-settings for typed, validated config with .env support.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration values for the Analytics gRPC service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # gRPC server
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50052
    grpc_max_workers: int = 10

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5433
    db_user: str = "stock_user"
    db_password: str = ""
    db_name: str = "stock_db"

    # DB pool size
    db_pool_min: int = 2
    db_pool_max: int = 10

    # Scheduler — recalculate after US market close (EST)
    enable_scheduler: bool = True
    calc_hour: int = 17    # 5 PM EST (30 min after regular close)
    calc_minute: int = 0

    # Logging
    log_level: str = "INFO"

    @property
    def grpc_address(self) -> str:
        return f"{self.grpc_host}:{self.grpc_port}"

    @property
    def db_dsn(self) -> dict:
        """Return psycopg2-compatible connection kwargs."""
        return {
            "host": self.db_host,
            "port": self.db_port,
            "user": self.db_user,
            "password": self.db_password,
            "dbname": self.db_name,
        }
