"""Tests for handlers/informer_handler.py — gRPC handler with mocked dependencies."""
from unittest.mock import MagicMock, patch

import grpc
import pandas as pd

from handlers.informer_handler import InformerHandler, _dict_to_stock, _dict_to_financial_report


class TestDictToStock:
    """_dict_to_stock converts a DB row dict to a proto Stock message."""

    def test_full_row(self, sample_stock_metadata):
        stock = _dict_to_stock(sample_stock_metadata)
        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.sector == "Technology"
        assert stock.market_cap == 3000000000000

    def test_missing_fields_default(self):
        stock = _dict_to_stock({})
        assert stock.symbol == ""
        assert stock.id == 0
        assert stock.is_active is True


class TestDictToFinancialReport:
    """_dict_to_financial_report converts row dict to proto FinancialReport."""

    def test_full_report(self, sample_financial_report):
        report = _dict_to_financial_report(sample_financial_report, "AAPL")
        assert report.symbol == "AAPL"
        assert report.revenue == 394328000000
        assert report.eps == 6.42

    def test_missing_fields_default_to_zero(self):
        report = _dict_to_financial_report({}, "TEST")
        assert report.symbol == "TEST"
        assert report.revenue == 0.0
        assert report.eps == 0.0


class TestInformerHandlerGetStockInfo:
    """GetStockInfo RPC — returns metadata or error codes."""

    def _make_handler(self, provider=None, stock_repo=None):
        return InformerHandler(
            provider=provider or MagicMock(),
            stock_repo=stock_repo or MagicMock(),
            ohlcv_repo=MagicMock(),
            financial_repo=MagicMock(),
        )

    def test_valid_symbol(self, mock_grpc_context, sample_stock_metadata):
        provider = MagicMock()
        provider.get_stock_metadata.return_value = sample_stock_metadata
        handler = self._make_handler(provider=provider)

        request = MagicMock()
        request.symbol = "AAPL"
        resp = handler.GetStockInfo(request, mock_grpc_context)

        assert resp.stock.symbol == "AAPL"
        mock_grpc_context.set_code.assert_not_called()

    def test_invalid_symbol(self, mock_grpc_context):
        handler = self._make_handler()
        request = MagicMock()
        request.symbol = "invalid123"
        handler.GetStockInfo(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_not_found(self, mock_grpc_context):
        provider = MagicMock()
        provider.get_stock_metadata.return_value = None
        handler = self._make_handler(provider=provider)

        request = MagicMock()
        request.symbol = "ZZZZ"
        handler.GetStockInfo(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_internal_error(self, mock_grpc_context):
        provider = MagicMock()
        provider.get_stock_metadata.side_effect = RuntimeError("db down")
        handler = self._make_handler(provider=provider)

        request = MagicMock()
        request.symbol = "AAPL"
        handler.GetStockInfo(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


class TestInformerHandlerListStocks:
    """ListStocks RPC — paginated search."""

    def test_returns_paginated_results(self, mock_grpc_context, sample_stock_metadata):
        stock_repo = MagicMock()
        stock_repo.search.return_value = ([sample_stock_metadata], 1)

        handler = InformerHandler(
            provider=MagicMock(),
            stock_repo=stock_repo,
            ohlcv_repo=MagicMock(),
            financial_repo=MagicMock(),
        )

        request = MagicMock()
        request.search = ""
        request.exchange = ""
        request.sector = ""
        request.pagination.page = 1
        request.pagination.page_size = 20

        resp = handler.ListStocks(request, mock_grpc_context)
        assert len(resp.stocks) == 1
        assert resp.pagination.total_count == 1


class TestInformerHandlerGetPriceHistory:
    """GetPriceHistory RPC — returns OHLCV candles."""

    def test_returns_candles(self, mock_grpc_context):
        df = pd.DataFrame([{
            "time": "2025-06-15",
            "open": 150.0, "high": 155.0, "low": 148.0,
            "close": 153.0, "volume": 1000000, "adjusted_close": 153.0,
        }])
        provider = MagicMock()
        provider.get_historical_ohlcv.return_value = df

        handler = InformerHandler(
            provider=provider,
            stock_repo=MagicMock(),
            ohlcv_repo=MagicMock(),
            financial_repo=MagicMock(),
        )

        request = MagicMock()
        request.symbol = "AAPL"
        request.start_date = "2025-01-01"
        request.end_date = "2025-12-31"
        request.limit = 0

        resp = handler.GetPriceHistory(request, mock_grpc_context)
        assert resp.symbol == "AAPL"
        assert len(resp.candles) == 1
        assert resp.candles[0].close == 153.0

    def test_empty_data(self, mock_grpc_context):
        provider = MagicMock()
        provider.get_historical_ohlcv.return_value = pd.DataFrame()

        handler = InformerHandler(
            provider=provider,
            stock_repo=MagicMock(),
            ohlcv_repo=MagicMock(),
            financial_repo=MagicMock(),
        )

        request = MagicMock()
        request.symbol = "AAPL"
        request.start_date = "2025-01-01"
        request.end_date = "2025-12-31"
        request.limit = 0

        resp = handler.GetPriceHistory(request, mock_grpc_context)
        assert resp.symbol == "AAPL"
        assert len(resp.candles) == 0


class TestInformerHandlerHealthCheck:
    """HealthCheck RPC — reports DB connectivity."""

    def test_healthy(self, mock_grpc_context):
        stock_repo = MagicMock()
        stock_repo._db.execute.return_value = {"result": 1}

        handler = InformerHandler(
            provider=MagicMock(),
            stock_repo=stock_repo,
            ohlcv_repo=MagicMock(),
            financial_repo=MagicMock(),
        )

        resp = handler.HealthCheck(MagicMock(), mock_grpc_context)
        assert resp.status == "SERVING"

    def test_unhealthy_db(self, mock_grpc_context):
        stock_repo = MagicMock()
        stock_repo._db.execute.side_effect = RuntimeError("conn refused")

        handler = InformerHandler(
            provider=MagicMock(),
            stock_repo=stock_repo,
            ohlcv_repo=MagicMock(),
            financial_repo=MagicMock(),
        )

        resp = handler.HealthCheck(MagicMock(), mock_grpc_context)
        assert resp.status == "NOT_SERVING"
