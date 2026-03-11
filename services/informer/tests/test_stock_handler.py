"""Tests for handlers/stock_handler.py — StockService RPCs with v1 proto types."""
import math
from unittest.mock import MagicMock

import grpc
import pytest

from handlers.stock_handler import StockHandler
from generated.informer.v1 import stock_pb2
from generated.common import pagination_pb2


@pytest.fixture
def mock_stock_repo():
    return MagicMock()


@pytest.fixture
def mock_provider():
    return MagicMock()


@pytest.fixture
def stock_handler(mock_provider, mock_stock_repo):
    return StockHandler(mock_provider, mock_stock_repo)


def _make_v1_stock(**kwargs):
    """Build a stock_pb2.Stock proto message with sensible defaults."""
    defaults = {
        "symbol": "TEST",
        "name": "Test Inc.",
        "sector": "Technology",
        "industry": "Software",
        "exchange": "NASDAQ",
        "country": "US",
        "currency": "USD",
        "is_active": True,
    }
    defaults.update(kwargs)
    return stock_pb2.Stock(**defaults)


# ─── GetStock ─────────────────────────────────────────────────────────────────

class TestGetStock:
    def test_valid_symbol_returns_stock(self, stock_handler, mock_provider, mock_grpc_context, sample_stock_metadata):
        mock_provider.get_stock_metadata.return_value = sample_stock_metadata
        request = MagicMock()
        request.symbol = "AAPL"

        resp = stock_handler.GetStock(request, mock_grpc_context)

        assert resp.stock.symbol == "AAPL"
        assert resp.stock.name == "Apple Inc."
        mock_grpc_context.set_code.assert_not_called()

    def test_invalid_symbol_returns_invalid_argument(self, stock_handler, mock_grpc_context):
        request = MagicMock()
        request.symbol = "!!!"

        stock_handler.GetStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_not_found_returns_not_found(self, stock_handler, mock_provider, mock_grpc_context):
        mock_provider.get_stock_metadata.return_value = None
        request = MagicMock()
        request.symbol = "ZZZZ"

        stock_handler.GetStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_provider_error_returns_internal(self, stock_handler, mock_provider, mock_grpc_context):
        mock_provider.get_stock_metadata.side_effect = RuntimeError("db down")
        request = MagicMock()
        request.symbol = "AAPL"

        stock_handler.GetStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── ListStocks ───────────────────────────────────────────────────────────────

class TestListStocks:
    def test_returns_paginated_results(self, stock_handler, mock_stock_repo, mock_grpc_context, sample_stock_metadata):
        mock_stock_repo.search.return_value = ([sample_stock_metadata], 1)
        request = MagicMock()
        request.search = ""
        request.exchange = ""
        request.sector = ""
        request.country = ""
        request.pagination.page = 1
        request.pagination.page_size = 20

        resp = stock_handler.ListStocks(request, mock_grpc_context)

        assert len(resp.stocks) == 1
        assert resp.stocks[0].symbol == "AAPL"
        assert resp.pagination.total_count == 1
        assert resp.pagination.total_pages == 1
        mock_grpc_context.set_code.assert_not_called()

    def test_repo_error_returns_internal(self, stock_handler, mock_stock_repo, mock_grpc_context):
        mock_stock_repo.search.side_effect = RuntimeError("query failed")
        request = MagicMock()
        request.search = ""
        request.exchange = ""
        request.sector = ""
        request.country = ""
        request.pagination.page = 1
        request.pagination.page_size = 20

        stock_handler.ListStocks(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── SearchStocks ─────────────────────────────────────────────────────────────

class TestSearchStocks:
    def test_returns_matching_stocks(self, stock_handler, mock_stock_repo, mock_grpc_context, sample_stock_metadata):
        mock_stock_repo.search.return_value = ([sample_stock_metadata], 1)
        request = MagicMock()
        request.query = "Apple"
        request.limit = 10

        resp = stock_handler.SearchStocks(request, mock_grpc_context)

        assert len(resp.stocks) == 1
        assert resp.stocks[0].symbol == "AAPL"
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_results(self, stock_handler, mock_stock_repo, mock_grpc_context):
        mock_stock_repo.search.return_value = ([], 0)
        request = MagicMock()
        request.query = "NOMATCH"
        request.limit = 10

        resp = stock_handler.SearchStocks(request, mock_grpc_context)

        assert len(resp.stocks) == 0
        mock_grpc_context.set_code.assert_not_called()


# ─── GetStocksByIds ───────────────────────────────────────────────────────────

class TestGetStocksByIds:
    def test_returns_stocks_for_ids(self, stock_handler, mock_stock_repo, mock_grpc_context, sample_stock_metadata):
        mock_stock_repo.get_by_ids.return_value = [sample_stock_metadata]
        request = MagicMock()
        request.ids = [1]

        resp = stock_handler.GetStocksByIds(request, mock_grpc_context)

        assert len(resp.stocks) == 1
        assert resp.stocks[0].symbol == "AAPL"
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_ids_returns_invalid_argument(self, stock_handler, mock_grpc_context):
        request = MagicMock()
        request.ids = []

        stock_handler.GetStocksByIds(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)


# ─── CreateStock ──────────────────────────────────────────────────────────────

class TestCreateStock:
    def test_valid_stock_creates_and_returns(self, stock_handler, mock_stock_repo, mock_grpc_context, sample_stock_metadata):
        mock_stock_repo.upsert.return_value = 1
        mock_stock_repo.get_by_id.return_value = sample_stock_metadata
        request = stock_pb2.CreateStockRequest(stock=_make_v1_stock())

        resp = stock_handler.CreateStock(request, mock_grpc_context)

        assert resp.stock.symbol == "AAPL"
        mock_stock_repo.upsert.assert_called_once()
        mock_grpc_context.set_code.assert_not_called()

    def test_empty_symbol_returns_invalid_argument(self, stock_handler, mock_grpc_context):
        request = stock_pb2.CreateStockRequest(stock=_make_v1_stock(symbol=""))

        stock_handler.CreateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_db_error_returns_internal(self, stock_handler, mock_stock_repo, mock_grpc_context):
        mock_stock_repo.upsert.side_effect = RuntimeError("DB down")
        request = stock_pb2.CreateStockRequest(stock=_make_v1_stock())

        stock_handler.CreateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── UpdateStock ──────────────────────────────────────────────────────────────

class TestUpdateStock:
    def test_update_existing_returns_updated(self, stock_handler, mock_stock_repo, mock_grpc_context, sample_stock_metadata):
        mock_stock_repo.get_by_symbol.return_value = sample_stock_metadata
        mock_stock_repo.upsert.return_value = 1
        mock_stock_repo.get_by_id.return_value = {**sample_stock_metadata, "name": "Apple Updated"}
        request = stock_pb2.UpdateStockRequest(symbol="AAPL", stock=_make_v1_stock(symbol="AAPL", name="Apple Updated"))

        resp = stock_handler.UpdateStock(request, mock_grpc_context)

        assert resp.stock.name == "Apple Updated"
        mock_grpc_context.set_code.assert_not_called()

    def test_not_found_returns_not_found(self, stock_handler, mock_stock_repo, mock_grpc_context):
        mock_stock_repo.get_by_symbol.return_value = None
        request = stock_pb2.UpdateStockRequest(symbol="ZZZZ", stock=_make_v1_stock(symbol="ZZZZ"))

        stock_handler.UpdateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_invalid_symbol_returns_invalid_argument(self, stock_handler, mock_grpc_context):
        request = stock_pb2.UpdateStockRequest(symbol="", stock=_make_v1_stock(symbol=""))

        stock_handler.UpdateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)


# ─── DeleteStock ──────────────────────────────────────────────────────────────

class TestDeleteStock:
    def test_delete_existing_returns_success(self, stock_handler, mock_stock_repo, mock_grpc_context):
        mock_stock_repo.soft_delete.return_value = True
        request = stock_pb2.DeleteStockRequest(symbol="AAPL")

        resp = stock_handler.DeleteStock(request, mock_grpc_context)

        assert resp.success is True
        assert "deactivated" in resp.message
        mock_grpc_context.set_code.assert_not_called()

    def test_delete_nonexistent_returns_not_found(self, stock_handler, mock_stock_repo, mock_grpc_context):
        mock_stock_repo.soft_delete.return_value = False
        request = stock_pb2.DeleteStockRequest(symbol="ZZZZ")

        resp = stock_handler.DeleteStock(request, mock_grpc_context)

        assert resp.success is False
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_invalid_symbol_returns_invalid_argument(self, stock_handler, mock_grpc_context):
        request = stock_pb2.DeleteStockRequest(symbol="")

        stock_handler.DeleteStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)


# ─── TriggerDataCollection ────────────────────────────────────────────────────

class TestTriggerDataCollection:
    def test_with_symbols_returns_accepted(self, stock_handler, mock_grpc_context):
        request = stock_pb2.TriggerDataCollectionRequest(
            symbols=["AAPL"], data_type="ohlcv", start_date="2024-01-01"
        )

        resp = stock_handler.TriggerDataCollection(request, mock_grpc_context)

        assert resp.accepted is True
        assert resp.job_id != ""
        mock_grpc_context.set_code.assert_not_called()

    def test_no_symbols_fetches_all_active(self, stock_handler, mock_stock_repo, mock_grpc_context):
        mock_stock_repo.get_all_active.return_value = [{"symbol": "AAPL"}, {"symbol": "MSFT"}]
        request = stock_pb2.TriggerDataCollectionRequest(symbols=[], data_type="ohlcv")

        resp = stock_handler.TriggerDataCollection(request, mock_grpc_context)

        assert resp.accepted is True
        mock_stock_repo.get_all_active.assert_called_once()
