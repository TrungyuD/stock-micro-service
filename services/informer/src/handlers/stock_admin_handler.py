"""
stock-admin-handler.py — gRPC handlers for stock CRUD operations.
Separated from informer_handler.py to keep files under 200 lines.
"""
import logging

import grpc

from generated import informer_pb2
from generated.common import types_pb2
from utils.validators import validate_symbol

logger = logging.getLogger(__name__)


def _stock_proto_to_dict(stock: types_pb2.Stock) -> dict:
    """Convert a proto Stock message to a plain dict for repository."""
    return {
        "symbol": stock.symbol.strip().upper() if stock.symbol else "",
        "name": stock.name or "",
        "sector": stock.sector or None,
        "industry": stock.industry or None,
        "exchange": stock.exchange or None,
        "country": stock.country or "US",
        "currency": stock.currency or "USD",
        "market_cap": stock.market_cap if stock.market_cap else None,
        "description": stock.description or None,
        "website": stock.website or None,
        "is_active": stock.is_active,
    }


def _dict_to_stock(row: dict) -> types_pb2.Stock:
    """Convert a stocks table row dict to a proto Stock message."""
    return types_pb2.Stock(
        id=row.get("id") or 0,
        symbol=row.get("symbol") or "",
        name=row.get("name") or "",
        sector=row.get("sector") or "",
        industry=row.get("industry") or "",
        exchange=row.get("exchange") or "",
        country=row.get("country") or "",
        currency=row.get("currency") or "",
        market_cap=row.get("market_cap") or 0,
        description=row.get("description") or "",
        website=row.get("website") or "",
        is_active=bool(row.get("is_active", True)),
    )


class StockAdminHandler:
    """Handles CreateStock, UpdateStock, DeleteStock RPCs."""

    def __init__(self, stock_repo) -> None:
        self._stock_repo = stock_repo

    def CreateStock(self, request, context):
        """Insert or upsert a new stock and return the created record."""
        stock_data = _stock_proto_to_dict(request.stock)
        symbol = stock_data.get("symbol", "")

        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.CreateStockResponse()

        try:
            stock_id = self._stock_repo.upsert(stock_data)
            row = self._stock_repo.get_by_id(stock_id)
            return informer_pb2.CreateStockResponse(stock=_dict_to_stock(row))
        except Exception as exc:
            logger.exception("CreateStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.CreateStockResponse()

    def UpdateStock(self, request, context):
        """Update an existing stock by symbol."""
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

            stock_data = _stock_proto_to_dict(request.stock)
            stock_data["symbol"] = symbol  # preserve original symbol
            stock_id = self._stock_repo.upsert(stock_data)
            row = self._stock_repo.get_by_id(stock_id)
            return informer_pb2.UpdateStockResponse(stock=_dict_to_stock(row))
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
