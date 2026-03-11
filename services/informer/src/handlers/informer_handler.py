"""
informer_handler.py — gRPC servicer implementing all InformerService RPCs.
Maps between proto messages and repository/provider data layer.
"""
import logging
import math
import threading
import uuid
from datetime import datetime, timezone

import grpc

from generated import informer_pb2, informer_pb2_grpc
from generated.common import types_pb2
from generated.common import health_pb2
from handlers import stock_admin_handler as _admin_mod
from handlers import live_price_handler as _live_price_mod
from mappers.stock_mapper import dict_to_stock
from utils.validators import validate_symbol

logger = logging.getLogger(__name__)

# Service version reported in HealthCheck
_VERSION = "1.0.0"
_START_TIME = datetime.now(timezone.utc)


class InformerHandler(informer_pb2_grpc.InformerServiceServicer):
    """
    Implements all RPCs defined in informer.proto.
    Delegates data access to repositories and HybridProvider.
    """

    def __init__(self, provider, stock_repo, ohlcv_repo, financial_repo) -> None:
        self._provider = provider
        self._stock_repo = stock_repo
        self._ohlcv_repo = ohlcv_repo
        self._financial_repo = financial_repo
        self._admin = _admin_mod.StockAdminHandler(stock_repo)

    # ─── GetStockInfo ─────────────────────────────────────────────────────────

    def GetStockInfo(self, request, context):
        """Return stock metadata; fetch from provider if not in DB."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.GetStockInfoResponse()

        try:
            data = self._provider.get_stock_metadata(symbol)
            if not data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Symbol not found: {symbol}")
                return informer_pb2.GetStockInfoResponse()
            return informer_pb2.GetStockInfoResponse(stock=dict_to_stock(data))
        except Exception as exc:
            logger.exception("GetStockInfo failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.GetStockInfoResponse()

    # ─── ListStocks ───────────────────────────────────────────────────────────

    def ListStocks(self, request, context):
        """Search stocks with optional filters and pagination."""
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
            return informer_pb2.ListStocksResponse(
                stocks=[dict_to_stock(r) for r in rows],
                pagination=types_pb2.PaginationResponse(
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
            return informer_pb2.ListStocksResponse()

    # ─── BatchGetStocks ───────────────────────────────────────────────────────

    def BatchGetStocks(self, request, context):
        """Fetch multiple stocks by symbol list; report not-found symbols."""
        # Validate, normalize, and deduplicate symbols upfront
        seen: set[str] = set()
        valid_symbols: list[str] = []
        invalid_symbols: list[str] = []
        for symbol in request.symbols:
            sym = symbol.strip().upper()
            if not validate_symbol(sym):
                invalid_symbols.append(symbol)
            elif sym not in seen:
                seen.add(sym)
                valid_symbols.append(sym)

        try:
            # Single batch query instead of N individual queries
            rows = self._stock_repo.get_by_symbols(valid_symbols)
            found_map = {r["symbol"]: r for r in rows}

            found = [dict_to_stock(found_map[s]) for s in valid_symbols if s in found_map]
            not_found = invalid_symbols + [s for s in valid_symbols if s not in found_map]
        except Exception as exc:
            logger.exception("BatchGetStocks failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.BatchGetStocksResponse()

        return informer_pb2.BatchGetStocksResponse(stocks=found, not_found=not_found)

    # ─── GetPriceHistory ──────────────────────────────────────────────────────

    def GetPriceHistory(self, request, context):
        """Return historical OHLCV bars for a symbol and date range."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.GetPriceHistoryResponse()

        start = request.start_date or "2015-01-01"
        end = request.end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        limit = request.limit or 0

        try:
            df = self._provider.get_historical_ohlcv(symbol, start, end)
            if df.empty:
                return informer_pb2.GetPriceHistoryResponse(symbol=symbol)

            rows = df.to_dict("records")
            if limit > 0:
                rows = rows[-limit:]  # keep most-recent N bars

            candles = [
                types_pb2.OHLCV(
                    date=str(r["time"]),
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    volume=int(r["volume"]),
                    adjusted_close=float(r["adjusted_close"]) if r.get("adjusted_close") is not None else 0.0,
                )
                for r in rows
            ]
            return informer_pb2.GetPriceHistoryResponse(
                symbol=symbol,
                candles=candles,
                total_records=len(candles),
                period_start=str(rows[0]["time"]) if rows else "",
                period_end=str(rows[-1]["time"]) if rows else "",
            )
        except Exception as exc:
            logger.exception("GetPriceHistory failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.GetPriceHistoryResponse()

    # ─── GetLivePrice ─────────────────────────────────────────────────────────

    def GetLivePrice(self, request, context):
        """Return real-time price snapshot for up to 20 symbols via yfinance."""
        symbols = list(request.symbols)
        if not symbols:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("symbols list must not be empty")
            return informer_pb2.GetLivePriceResponse()

        try:
            return _live_price_mod.get_live_prices(symbols)
        except Exception as exc:
            logger.exception("GetLivePrice failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.GetLivePriceResponse()

    # ─── GetFinancialReport ───────────────────────────────────────────────────

    def GetFinancialReport(self, request, context):
        """Return the latest financial report of a given type for a symbol."""
        symbol = request.symbol.strip().upper()
        report_type = request.report_type or "Annual"

        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.GetFinancialReportResponse()

        try:
            stock_row = self._stock_repo.get_by_symbol(symbol)
            if stock_row:
                row = self._financial_repo.get_latest(stock_row["id"], report_type)
                if row:
                    return informer_pb2.GetFinancialReportResponse(
                        report=_dict_to_financial_report(row, symbol)
                    )

            # Not in DB — fetch from provider
            reports = self._provider.get_financial_reports(symbol)
            matching = [r for r in reports if r.get("report_type") == report_type]
            if not matching:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"No {report_type} report found for {symbol}")
                return informer_pb2.GetFinancialReportResponse()

            latest = sorted(matching, key=lambda r: r["report_date"], reverse=True)[0]
            return informer_pb2.GetFinancialReportResponse(
                report=_dict_to_financial_report(latest, symbol)
            )
        except Exception as exc:
            logger.exception("GetFinancialReport failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.GetFinancialReportResponse()

    # ─── GetFinancialReports ──────────────────────────────────────────────────

    def GetFinancialReports(self, request, context):
        """Return historical financial reports for a symbol."""
        symbol = request.symbol.strip().upper()
        report_type = request.report_type or "Annual"
        years_back = request.years_back or 5

        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return informer_pb2.GetFinancialReportsResponse()

        try:
            stock_row = self._stock_repo.get_by_symbol(symbol)
            if stock_row:
                rows = self._financial_repo.get_history(
                    stock_row["id"], report_type, years_back
                )
                if rows:
                    return informer_pb2.GetFinancialReportsResponse(
                        reports=[_dict_to_financial_report(r, symbol) for r in rows]
                    )

            reports = self._provider.get_financial_reports(symbol)
            matching = [r for r in reports if r.get("report_type") == report_type]
            return informer_pb2.GetFinancialReportsResponse(
                reports=[_dict_to_financial_report(r, symbol) for r in matching]
            )
        except Exception as exc:
            logger.exception("GetFinancialReports failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return informer_pb2.GetFinancialReportsResponse()

    # ─── TriggerDataCollection ────────────────────────────────────────────────

    def TriggerDataCollection(self, request, context):
        """
        Admin RPC: enqueue a background data-collection job for given symbols.
        Spawns a daemon thread; returns a job_id immediately (fire-and-forget).
        """
        symbols = [s.strip().upper() for s in request.symbols if s.strip()]
        data_type = request.data_type or "ohlcv"
        start_date = request.start_date or "2020-01-01"

        if not symbols:
            # Collect all active stocks when no symbols specified
            try:
                rows = self._stock_repo.get_all_active()
                symbols = [r["symbol"] for r in rows]
            except Exception as exc:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(exc))
                return informer_pb2.TriggerDataCollectionResponse(accepted=False)

        job_id = str(uuid.uuid4())
        logger.info(
            "TriggerDataCollection job_id=%s type=%s symbols=%d start=%s",
            job_id, data_type, len(symbols), start_date,
        )

        # Run in background daemon thread so gRPC response is immediate
        thread = threading.Thread(
            target=self._run_collection_job,
            args=(job_id, symbols, data_type, start_date),
            daemon=True,
            name=f"collect-{job_id[:8]}",
        )
        thread.start()

        return informer_pb2.TriggerDataCollectionResponse(
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

    # ─── HealthCheck ──────────────────────────────────────────────────────────

    def HealthCheck(self, request, context):
        """Return service status and DB connectivity check."""
        # Probe DB with a lightweight query
        db_ok = False
        try:
            self._stock_repo._db.execute("SELECT 1", fetch="one")
            db_ok = True
        except Exception as exc:
            logger.warning("HealthCheck DB probe failed: %s", exc)

        status = "SERVING" if db_ok else "NOT_SERVING"
        uptime_secs = (datetime.now(timezone.utc) - _START_TIME).total_seconds()
        uptime_str = f"{int(uptime_secs)}s"

        return health_pb2.HealthCheckResponse(
            status=status,
            version=_VERSION,
            uptime=uptime_str,
        )

    # ─── Stock Admin CRUD (delegated) ──────────────────────────────────────────

    def CreateStock(self, request, context):
        return self._admin.CreateStock(request, context)

    def UpdateStock(self, request, context):
        return self._admin.UpdateStock(request, context)

    def DeleteStock(self, request, context):
        return self._admin.DeleteStock(request, context)


# ─── proto mapping helpers ────────────────────────────────────────────────────
# dict_to_stock moved to mappers/stock_mapper.py


def _dict_to_financial_report(row: dict, symbol: str) -> informer_pb2.FinancialReport:
    """Convert a `financial_reports` row dict to a proto FinancialReport message."""
    def _f(key: str) -> float:
        v = row.get(key)
        return float(v) if v is not None else 0.0

    def _i(key: str) -> int:
        v = row.get(key)
        return int(v) if v is not None else 0

    return informer_pb2.FinancialReport(
        symbol=symbol,
        report_date=str(row.get("report_date") or ""),
        report_type=str(row.get("report_type") or ""),
        revenue=_f("revenue"),
        gross_profit=_f("gross_profit"),
        operating_income=_f("operating_income"),
        net_income=_f("net_income"),
        eps=_f("eps"),
        total_assets=_f("total_assets"),
        total_liabilities=_f("total_liabilities"),
        shareholders_equity=_f("shareholders_equity"),
        book_value_per_share=_f("book_value_per_share"),
        operating_cash_flow=_f("operating_cash_flow"),
        free_cash_flow=_f("free_cash_flow"),
        capex=_f("capex"),
        shares_outstanding=_i("shares_outstanding"),
        debt_to_equity=_f("debt_to_equity"),
        current_ratio=_f("current_ratio"),
        roe=_f("roe"),
        roa=_f("roa"),
    )
