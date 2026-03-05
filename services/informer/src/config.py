"""
config.py — Informer service configuration loaded from environment variables.
Uses pydantic-settings for typed, validated config with .env support.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration values for the Informer gRPC service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # gRPC server
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    grpc_max_workers: int = 10

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "stock_user"
    db_password: str = ""
    db_name: str = "stock_db"
    db_pool_min: int = 2
    db_pool_max: int = 10

    # yfinance
    yfinance_timeout: int = 30
    yfinance_max_retries: int = 3

    # Alpha Vantage (optional fallback)
    alpha_vantage_key: str = ""

    # Scheduler
    enable_scheduler: bool = True
    collection_hour: int = 16    # 4 PM EST
    collection_minute: int = 30

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


# Singleton settings instance used across the service
settings = Settings()
