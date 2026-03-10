"""Tests for handlers/stock_admin_handler.py — CreateStock, UpdateStock, DeleteStock."""
from unittest.mock import MagicMock, patch

import grpc
import pytest

from handlers.stock_admin_handler import StockAdminHandler
from generated import informer_pb2
from generated.common import types_pb2


@pytest.fixture
def mock_stock_repo():
    return MagicMock()


@pytest.fixture
def admin_handler(mock_stock_repo):
    return StockAdminHandler(mock_stock_repo)


def _make_stock_proto(**kwargs):
    """Build a types_pb2.Stock proto message."""
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
    return types_pb2.Stock(**defaults)


class TestCreateStock:
    def test_create_valid_stock(self, admin_handler, mock_stock_repo, mock_grpc_context):
        """CreateStock with valid data returns created stock."""
        mock_stock_repo.upsert.return_value = 42
        mock_stock_repo.get_by_id.return_value = {
            "id": 42, "symbol": "TEST", "name": "Test Inc.",
            "sector": "Technology", "industry": "Software",
            "exchange": "NASDAQ", "country": "US", "currency": "USD",
            "is_active": True,
        }

        request = informer_pb2.CreateStockRequest(stock=_make_stock_proto())
        response = admin_handler.CreateStock(request, mock_grpc_context)

        assert response.stock.symbol == "TEST"
        mock_stock_repo.upsert.assert_called_once()
        mock_grpc_context.set_code.assert_not_called()

    def test_create_empty_symbol(self, admin_handler, mock_grpc_context):
        """CreateStock with empty symbol returns INVALID_ARGUMENT."""
        request = informer_pb2.CreateStockRequest(stock=_make_stock_proto(symbol=""))
        response = admin_handler.CreateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_create_db_error(self, admin_handler, mock_stock_repo, mock_grpc_context):
        """CreateStock with DB error returns INTERNAL."""
        mock_stock_repo.upsert.side_effect = RuntimeError("DB down")

        request = informer_pb2.CreateStockRequest(stock=_make_stock_proto())
        response = admin_handler.CreateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


class TestUpdateStock:
    def test_update_existing(self, admin_handler, mock_stock_repo, mock_grpc_context):
        """UpdateStock on existing stock returns updated stock."""
        existing = {
            "id": 1, "symbol": "TEST", "name": "Old Name",
            "sector": "Tech", "industry": "SW", "exchange": "NASDAQ",
            "country": "US", "currency": "USD", "is_active": True,
        }
        mock_stock_repo.get_by_symbol.return_value = existing
        mock_stock_repo.upsert.return_value = 1
        mock_stock_repo.get_by_id.return_value = {**existing, "name": "New Name"}

        request = informer_pb2.UpdateStockRequest(
            symbol="TEST",
            stock=_make_stock_proto(name="New Name"),
        )
        response = admin_handler.UpdateStock(request, mock_grpc_context)

        assert response.stock.name == "New Name"
        mock_grpc_context.set_code.assert_not_called()

    def test_update_nonexistent(self, admin_handler, mock_stock_repo, mock_grpc_context):
        """UpdateStock on nonexistent stock returns NOT_FOUND."""
        mock_stock_repo.get_by_symbol.return_value = None

        request = informer_pb2.UpdateStockRequest(
            symbol="ZZZZ",
            stock=_make_stock_proto(symbol="ZZZZ"),
        )
        response = admin_handler.UpdateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_update_invalid_symbol(self, admin_handler, mock_grpc_context):
        """UpdateStock with invalid symbol returns INVALID_ARGUMENT."""
        request = informer_pb2.UpdateStockRequest(
            symbol="",
            stock=_make_stock_proto(symbol=""),
        )
        response = admin_handler.UpdateStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_update_is_active_false(self, admin_handler, mock_stock_repo, mock_grpc_context):
        """UpdateStock with is_active=False correctly deactivates stock."""
        existing = {
            "id": 1, "symbol": "TEST", "name": "Test Inc.",
            "sector": "Tech", "industry": "SW", "exchange": "NASDAQ",
            "country": "US", "currency": "USD", "is_active": True,
        }
        mock_stock_repo.get_by_symbol.return_value = existing
        mock_stock_repo.upsert.return_value = 1
        mock_stock_repo.get_by_id.return_value = {**existing, "is_active": False}

        request = informer_pb2.UpdateStockRequest(
            symbol="TEST",
            stock=_make_stock_proto(is_active=False),
        )
        response = admin_handler.UpdateStock(request, mock_grpc_context)

        assert response.stock.is_active is False
        # Verify upsert received is_active=False
        upsert_data = mock_stock_repo.upsert.call_args[0][0]
        assert upsert_data["is_active"] is False
        mock_grpc_context.set_code.assert_not_called()


class TestDeleteStock:
    def test_delete_existing(self, admin_handler, mock_stock_repo, mock_grpc_context):
        """DeleteStock on existing stock returns success=True."""
        mock_stock_repo.soft_delete.return_value = True

        request = informer_pb2.DeleteStockRequest(symbol="TEST")
        response = admin_handler.DeleteStock(request, mock_grpc_context)

        assert response.success is True
        assert "deactivated" in response.message
        mock_grpc_context.set_code.assert_not_called()

    def test_delete_nonexistent(self, admin_handler, mock_stock_repo, mock_grpc_context):
        """DeleteStock on nonexistent stock returns NOT_FOUND."""
        mock_stock_repo.soft_delete.return_value = False

        request = informer_pb2.DeleteStockRequest(symbol="ZZZZ")
        response = admin_handler.DeleteStock(request, mock_grpc_context)

        assert response.success is False
        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_delete_invalid_symbol(self, admin_handler, mock_grpc_context):
        """DeleteStock with invalid symbol returns INVALID_ARGUMENT."""
        request = informer_pb2.DeleteStockRequest(symbol="")
        response = admin_handler.DeleteStock(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)
