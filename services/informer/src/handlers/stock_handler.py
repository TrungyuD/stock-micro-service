"""
stock_handler.py — StockService gRPC handler. Stock metadata CRUD and queries.
Implements StockServiceServicer from generated.informer.v1.stock_pb2_grpc.
"""
import logging
import math
import threading
import uuid
from datetime import datetime, timezone

import grpc

from generated.informer.v1 import stock_pb2, stock_pb2_grpc
from generated.common import pagination_pb2
from mappers.stock_mapper import dict_to_stock, stock_proto_to_dict
from utils.validators import validate_symbol

logger = logging.getLogger(__name__)


class StockHandler(stock_pb2_grpc.StockServiceServicer):
    """
    Implements all RPCs defined in stock.proto (StockService).
    Handles stock metadata CRUD, search, and data collection trigger.
    """

    def __init__(self, provider, stock_repo) -> None:
        self._provider = provider
        self._stock_repo = stock_repo

    # ─── GetStock ─────────────────────────────────────────────────────────────

    def GetStock(self, request, context):
        """Return stock metadata; fetch from provider if not in DB."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return stock_pb2.GetStockResponse()

        try:
            data = self._provider.get_stock_metadata(symbol)
            if not data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found: {symbol}")
                return stock_pb2.GetStockResponse()
            return stock_pb2.GetStockResponse(stock=dict_to_stock(data))
        except Exception as exc:
            logger.exception("GetStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stock_pb2.GetStockResponse()

    # ─── ListStocks ───────────────────────────────────────────────────────────

    def ListStocks(self, request, context):
        """List stocks with filters and pagination."""
        page = request.pagination.page or 1
        page_size = request.pagination.page_size or 20

        try:
            rows, total = self._stock_repo.search(
                query=request.search,
                exchange=request.exchange,
                sector=request.sector,
                country=request.country,
                page=page,
                page_size=page_size,
            )
            total_pages = math.ceil(total / page_size) if page_size else 1
            return stock_pb2.ListStocksResponse(
                stocks=[dict_to_stock(r) for r in rows],
                pagination=pagination_pb2.PaginationResponse(
                    total_count=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                ),
            )
        except Exception as exc:
            logger.exception("ListStocks failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stock_pb2.ListStocksResponse()

    # ─── SearchStocks ─────────────────────────────────────────────────────────

    def SearchStocks(self, request, context):
        """Search stocks by name or symbol substring with optional limit."""
        query = request.query.strip()
        limit = request.limit or 20

        try:
            rows, _ = self._stock_repo.search(query=query, page=1, page_size=limit)
            return stock_pb2.StockListResponse(stocks=[dict_to_stock(r) for r in rows])
        except Exception as exc:
            logger.exception("SearchStocks failed for query=%s", query)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stock_pb2.StockListResponse()

    # ─── GetStocksByIds ───────────────────────────────────────────────────────

    def GetStocksByIds(self, request, context):
        """Batch fetch stocks by their primary-key IDs. Max 100 IDs."""
        ids = list(request.ids)
        if not ids:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("ids list must not be empty")
            return stock_pb2.StockListResponse()

        try:
            rows = self._stock_repo.get_by_ids(ids[:100])  # cap at 100
            return stock_pb2.StockListResponse(stocks=[dict_to_stock(r) for r in rows])
        except Exception as exc:
            logger.exception("GetStocksByIds failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stock_pb2.StockListResponse()

    # ─── CreateStock ──────────────────────────────────────────────────────────

    def CreateStock(self, request, context):
        """Insert or upsert a new stock and return the created record."""
        stock_data = stock_proto_to_dict(request.stock)
        symbol = stock_data.get("symbol", "")

        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return stock_pb2.StockResponse()

        try:
            stock_id = self._stock_repo.upsert(stock_data)
            row = self._stock_repo.get_by_id(stock_id)
            return stock_pb2.StockResponse(stock=dict_to_stock(row))
        except Exception as exc:
            logger.exception("CreateStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stock_pb2.StockResponse()

    # ─── UpdateStock ──────────────────────────────────────────────────────────

    def UpdateStock(self, request, context):
        """Update an existing stock by symbol (partial update — merges with existing)."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return stock_pb2.StockResponse()

        try:
            existing = self._stock_repo.get_by_symbol(symbol)
            if not existing:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Stock not found: {symbol}")
                return stock_pb2.StockResponse()

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
            return stock_pb2.StockResponse(stock=dict_to_stock(row))
        except Exception as exc:
            logger.exception("UpdateStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stock_pb2.StockResponse()

    # ─── DeleteStock ──────────────────────────────────────────────────────────

    def DeleteStock(self, request, context):
        """Soft-delete a stock (set is_active=FALSE)."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return stock_pb2.DeleteStockResponse(success=False)

        try:
            deleted = self._stock_repo.soft_delete(symbol)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Stock not found: {symbol}")
                return stock_pb2.DeleteStockResponse(
                    success=False, message=f"Stock not found: {symbol}"
                )
            return stock_pb2.DeleteStockResponse(
                success=True, message=f"Stock {symbol} deactivated"
            )
        except Exception as exc:
            logger.exception("DeleteStock failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return stock_pb2.DeleteStockResponse(success=False)

    # ─── TriggerDataCollection ────────────────────────────────────────────────

    def TriggerDataCollection(self, request, context):
        """Admin RPC: enqueue a background data-collection job. Fire-and-forget."""
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        data_type = request.data_type or "ohlcv"
        start_date = request.start_date or "2020-01-01"

        if not symbols:
            try:
                rows = self._stock_repo.get_all_active()
                symbols = [r["symbol"] for r in rows]
            except Exception as exc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(exc))
                return stock_pb2.TriggerDataCollectionResponse(accepted=False)

        job_id = str(uuid.uuid4())
        logger.info(
            "TriggerDataCollection job_id=%s type=%s symbols=%d start=%s",
            job_id, data_type, len(symbols), start_date,
        )

        thread = threading.Thread(
            target=self._run_collection_job,
            args=(job_id, symbols, data_type, start_date),
            daemon=True,
            name=f"collect-{job_id[:8]}",
        )
        thread.start()

        return stock_pb2.TriggerDataCollectionResponse(
            accepted=True,
            job_id=job_id,
            message=f"Collecting {data_type} for {len(symbols)} symbol(s)",
        )

    def _run_collection_job(
        self, job_id: str, symbols: list, data_type: str, start_date: str
    ) -> None:
        """Background worker for TriggerDataCollection."""
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for symbol in symbols:
            try:
                if data_type in ("ohlcv", "all"):
                    df = self._provider.get_historical_ohlcv(symbol, start_date, end_date)
                    logger.info("job=%s OHLCV %s → %d bars", job_id, symbol, len(df))
                if data_type in ("metadata", "all"):
                    self._provider.get_stock_metadata(symbol)
                    logger.info("job=%s metadata %s done", job_id, symbol)
                if data_type in ("financials", "all"):
                    reports = self._provider.get_financial_reports(symbol)
                    logger.info("job=%s financials %s → %d reports", job_id, symbol, len(reports))
            except Exception as exc:
                logger.error("job=%s failed for %s: %s", job_id, symbol, exc)
        logger.info("TriggerDataCollection job_id=%s complete", job_id)
