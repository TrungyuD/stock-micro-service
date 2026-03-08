"""Shared fixtures for Informer service tests."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src/ to path so imports like `from utils.validators import ...` work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def sample_stock_metadata():
    """Realistic stock metadata dict matching provider output."""
    return {
        "id": 1,
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "exchange": "NASDAQ",
        "country": "US",
        "currency": "USD",
        "market_cap": 3000000000000,
        "description": "Apple designs consumer electronics.",
        "website": "https://apple.com",
        "is_active": True,
    }


@pytest.fixture
def sample_ohlcv_row():
    """Single OHLCV candle dict."""
    return {
        "time": "2025-06-15",
        "open": 150.0,
        "high": 155.0,
        "low": 148.0,
        "close": 153.0,
        "volume": 1000000,
        "adjusted_close": 153.0,
    }


@pytest.fixture
def sample_financial_report():
    """Financial report dict matching provider output."""
    return {
        "report_date": "2025-12-31",
        "report_type": "Annual",
        "revenue": 394328000000,
        "net_income": 96995000000,
        "eps": 6.42,
        "total_assets": 352583000000,
        "total_liabilities": 290437000000,
        "book_value_per_share": 4.38,
        "shares_outstanding": 15115000000,
        "operating_cash_flow": 118254000000,
        "free_cash_flow": 107582000000,
    }


@pytest.fixture
def mock_db_pool():
    """Mock database pool with execute method."""
    pool = MagicMock()
    pool.execute = MagicMock()
    return pool


@pytest.fixture
def mock_grpc_context():
    """Mock gRPC servicer context."""
    ctx = MagicMock()
    ctx.set_code = MagicMock()
    ctx.set_details = MagicMock()
    return ctx
