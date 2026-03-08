"""Shared fixtures for Analytics service tests."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src/ to path so imports like `from calculators.technical_calculator import ...` work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def sample_bars_300():
    """300 OHLCV bar dicts with realistic upward-trending prices."""
    bars = []
    base = 100.0
    for i in range(300):
        close = base + i * 0.5
        bars.append({
            "open": close - 0.3,
            "high": close + 1.5,
            "low": close - 1.0,
            "close": close,
            "volume": 1000000 + i * 1000,
        })
    return bars


@pytest.fixture
def sample_bars_short():
    """Only 5 bars — insufficient for most indicators."""
    return [{"close": 100 + i} for i in range(5)]


@pytest.fixture
def sample_latest_report():
    """Minimal financial report dict for valuation tests."""
    return {
        "eps": 6.42,
        "book_value_per_share": 4.38,
        "shares_outstanding": 15115000000,
        "revenue": 394328000000,
        "operating_income": 114301000000,
        "net_income": 96995000000,
        "report_date": "2025-12-31",
    }


@pytest.fixture
def sample_eps_history():
    """5 years of EPS history for growth rate calculation."""
    return [
        {"report_date": "2021-12-31", "eps": 4.0},
        {"report_date": "2022-12-31", "eps": 4.5},
        {"report_date": "2023-12-31", "eps": 5.2},
        {"report_date": "2024-12-31", "eps": 5.8},
        {"report_date": "2025-12-31", "eps": 6.42},
    ]


@pytest.fixture
def sample_revenue_history():
    """4 years of revenue history."""
    return [
        {"revenue": 300000000000, "operating_income": 90000000000, "shares_outstanding": 15115000000},
        {"revenue": 330000000000, "operating_income": 95000000000, "shares_outstanding": 15115000000},
        {"revenue": 370000000000, "operating_income": 110000000000, "shares_outstanding": 15115000000},
        {"revenue": 394328000000, "operating_income": 114301000000, "shares_outstanding": 15115000000},
    ]


@pytest.fixture
def mock_grpc_context():
    """Mock gRPC context."""
    ctx = MagicMock()
    ctx.set_code = MagicMock()
    ctx.set_details = MagicMock()
    return ctx
