"""
stock_admin_handler.py — gRPC handlers for stock CRUD operations.
Separated from informer_handler.py to keep files under 200 lines.
"""
import logging

import grpc

from generated import informer_pb2
from generated.common import types_pb2
from mappers.legacy_stock_mapper import dict_to_legacy_stock as dict_to_stock, stock_legacy_proto_to_dict as stock_proto_to_dict
from utils.validators import validate_symbol

logger = logging.getLogger(__name__)


class StockAdminHandler:
    """Handles CreateStock, UpdateStock, DeleteStock RPCs."""

    def __init__(self, stock_repo) -> None:
        self._stock_repo = stock_repo

    def CreateStock(self, request, context):
        """Insert or upsert a new stock and return the created record."""
        stock_data = stock_proto_to_dict(request.stock)
        symbol = stock_data.get("symbol", "")

        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.CreateStockResponse()

        try:
            stock_id = self._stock_repo.upsert(stock_data)
            row = self._stock_repo.get_by_id(stock_id)
            return informer_pb2.CreateStockResponse(stock=dict_to_stock(row))
        except Exception as exc:
            logger.exception("CreateStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.CreateStockResponse()

    def UpdateStock(self, request, context):
        """Update an existing stock by symbol. Merges with existing data (partial update)."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.UpdateStockResponse()

        try:
            existing = self._stock_repo.get_by_symbol(symbol)
            if not existing:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Stock not found: {symbol}")
                return informer_pb2.UpdateStockResponse()

            # Merge incoming fields with existing data (partial update)
            incoming = stock_proto_to_dict(request.stock)
            stock_data = {
                "symbol": symbol,
                "name": incoming["name"] or existing.get("name", ""),
                "sector": incoming["sector"] if incoming["sector"] is not None else existing.get("sector"),
                "industry": incoming["industry"] if incoming["industry"] is not None else existing.get("industry"),
                "exchange": incoming["exchange"] if incoming["exchange"] is not None else existing.get("exchange"),
                "country": incoming["country"] or existing.get("country", "US"),
                "currency": incoming["currency"] or existing.get("currency", "USD"),
                "market_cap": incoming["market_cap"] or existing.get("market_cap"),
                "description": incoming["description"] if incoming["description"] is not None else existing.get("description"),
                "website": incoming["website"] if incoming["website"] is not None else existing.get("website"),
                "is_active": incoming["is_active"],
            }
            stock_id = self._stock_repo.upsert(stock_data)
            row = self._stock_repo.get_by_id(stock_id)
            return informer_pb2.UpdateStockResponse(stock=dict_to_stock(row))
        except Exception as exc:
            logger.exception("UpdateStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.UpdateStockResponse()

    def DeleteStock(self, request, context):
        """Soft-delete a stock (set is_active=FALSE)."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.DeleteStockResponse(success=False)

        try:
            deleted = self._stock_repo.soft_delete(symbol)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Stock not found: {symbol}")
                return informer_pb2.DeleteStockResponse(
                    success=False, message=f"Stock not found: {symbol}"
                )
            return informer_pb2.DeleteStockResponse(
                success=True, message=f"Stock {symbol} deactivated"
            )
        except Exception as exc:
            logger.exception("DeleteStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.DeleteStockResponse(success=False)
