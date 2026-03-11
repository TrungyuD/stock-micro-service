"""
financial_handler.py — FinancialService gRPC handler. Financial report retrieval.
Implements FinancialServiceServicer from generated.informer.v1.financial_pb2_grpc.
"""
import logging

import grpc

from generated.informer.v1 import financial_pb2, financial_pb2_grpc
from utils.validators import validate_symbol

logger = logging.getLogger(__name__)

# Default years of history to fetch when not specified by caller
_DEFAULT_YEARS_BACK = 5


class FinancialHandler(financial_pb2_grpc.FinancialServiceServicer):
    """
    Implements all RPCs defined in financial.proto (FinancialService).
    Fetches financial reports from DB first, falls back to provider.
    """

    def __init__(self, provider, stock_repo, financial_repo) -> None:
        self._provider = provider
        self._stock_repo = stock_repo
        self._financial_repo = financial_repo

    # ─── GetIncomeStatement ───────────────────────────────────────────────────

    def GetIncomeStatement(self, request, context):
        """Return income statement entries for a symbol."""
        symbol, period, years_back = _parse_request(request)
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return financial_pb2.IncomeStatementResponse()

        try:
            reports = self._get_reports(symbol, period, years_back)
            statements = [
                financial_pb2.IncomeStatement(
                    report_date=str(r.get("report_date") or ""),
                    period=str(r.get("report_type") or period),
                    revenue=_f(r, "revenue"),
                    gross_profit=_f(r, "gross_profit"),
                    operating_income=_f(r, "operating_income"),
                    net_income=_f(r, "net_income"),
                    eps=_f(r, "eps"),
                )
                for r in reports
            ]
            return financial_pb2.IncomeStatementResponse(symbol=symbol, statements=statements)
        except Exception as exc:
            logger.exception("GetIncomeStatement failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return financial_pb2.IncomeStatementResponse()

    # ─── GetBalanceSheet ──────────────────────────────────────────────────────

    def GetBalanceSheet(self, request, context):
        """Return balance sheet entries for a symbol."""
        symbol, period, years_back = _parse_request(request)
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return financial_pb2.BalanceSheetResponse()

        try:
            reports = self._get_reports(symbol, period, years_back)
            sheets = [
                financial_pb2.BalanceSheet(
                    report_date=str(r.get("report_date") or ""),
                    period=str(r.get("report_type") or period),
                    total_assets=_f(r, "total_assets"),
                    total_liabilities=_f(r, "total_liabilities"),
                    shareholders_equity=_f(r, "shareholders_equity"),
                    book_value_per_share=_f(r, "book_value_per_share"),
                    debt_to_equity=_f(r, "debt_to_equity"),
                    current_ratio=_f(r, "current_ratio"),
                )
                for r in reports
            ]
            return financial_pb2.BalanceSheetResponse(symbol=symbol, sheets=sheets)
        except Exception as exc:
            logger.exception("GetBalanceSheet failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return financial_pb2.BalanceSheetResponse()

    # ─── GetCashFlow ──────────────────────────────────────────────────────────

    def GetCashFlow(self, request, context):
        """Return cash flow statement entries for a symbol."""
        symbol, period, years_back = _parse_request(request)
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return financial_pb2.CashFlowResponse()

        try:
            reports = self._get_reports(symbol, period, years_back)
            flows = [
                financial_pb2.CashFlowStatement(
                    report_date=str(r.get("report_date") or ""),
                    period=str(r.get("report_type") or period),
                    operating_cash_flow=_f(r, "operating_cash_flow"),
                    free_cash_flow=_f(r, "free_cash_flow"),
                    capex=_f(r, "capex"),
                )
                for r in reports
            ]
            return financial_pb2.CashFlowResponse(symbol=symbol, flows=flows)
        except Exception as exc:
            logger.exception("GetCashFlow failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return financial_pb2.CashFlowResponse()

    # ─── GetFinancialSummary ──────────────────────────────────────────────────

    def GetFinancialSummary(self, request, context):
        """Return combined key metrics from the most recent annual report."""
        symbol = request.symbol.strip().upper()
        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return financial_pb2.FinancialSummaryResponse()

        try:
            # Fetch the single most-recent annual report for summary metrics
            reports = self._get_reports(symbol, period="Annual", years_back=1)
            if not reports:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"No financial data found for {symbol}")
                return financial_pb2.FinancialSummaryResponse()

            r = reports[0]  # most recent
            summary = financial_pb2.FinancialSummary(
                symbol=symbol,
                revenue=_f(r, "revenue"),
                net_income=_f(r, "net_income"),
                eps=_f(r, "eps"),
                roe=_f(r, "roe"),
                roa=_f(r, "roa"),
                debt_to_equity=_f(r, "debt_to_equity"),
                current_ratio=_f(r, "current_ratio"),
                free_cash_flow=_f(r, "free_cash_flow"),
                shares_outstanding=_i(r, "shares_outstanding"),
                latest_report_date=str(r.get("report_date") or ""),
            )
            return financial_pb2.FinancialSummaryResponse(summary=summary)
        except Exception as exc:
            logger.exception("GetFinancialSummary failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return financial_pb2.FinancialSummaryResponse()

    # ─── GetFinancialReports (backward-compat) ────────────────────────────────

    def GetFinancialReports(self, request, context):
        """Return full historical financial reports (all fields). Backward-compatible RPC."""
        symbol = request.symbol.strip().upper()
        report_type = request.report_type or "Annual"
        years_back = request.years_back or _DEFAULT_YEARS_BACK

        if not validate_symbol(symbol):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid symbol: '{symbol}'")
            return financial_pb2.GetFinancialReportsResponse()

        try:
            reports = self._get_reports(symbol, period=report_type, years_back=years_back)
            protos = [_dict_to_financial_report(r, symbol) for r in reports]
            return financial_pb2.GetFinancialReportsResponse(reports=protos)
        except Exception as exc:
            logger.exception("GetFinancialReports failed for %s", symbol)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return financial_pb2.GetFinancialReportsResponse()

    # ─── shared internal helper ───────────────────────────────────────────────

    def _get_reports(self, symbol: str, period: str, years_back: int) -> list[dict]:
        """
        Fetch financial reports from DB first; fall back to provider if empty.
        Returns list of report dicts sorted newest-first.
        """
        stock_row = self._stock_repo.get_by_symbol(symbol)
        if stock_row:
            rows = self._financial_repo.get_history(stock_row["id"], period, years_back)
            if rows:
                return rows

        # DB miss — fetch from provider and filter by period
        all_reports = self._provider.get_financial_reports(symbol)
        matching = [r for r in all_reports if r.get("report_type") == period]
        return sorted(matching, key=lambda r: r.get("report_date", ""), reverse=True)


# ─── proto mapping helpers ────────────────────────────────────────────────────

def _f(row: dict, key: str) -> float:
    """Extract float from report dict, defaulting to 0.0."""
    v = row.get(key)
    return float(v) if v is not None else 0.0


def _i(row: dict, key: str) -> int:
    """Extract int from report dict, defaulting to 0."""
    v = row.get(key)
    return int(v) if v is not None else 0


def _parse_request(request) -> tuple[str, str, int]:
    """Extract and normalize common fields from GetFinancialRequest."""
    symbol = request.symbol.strip().upper()
    period = request.period or "Annual"
    years_back = request.years_back or _DEFAULT_YEARS_BACK
    return symbol, period, years_back


def _dict_to_financial_report(row: dict, symbol: str) -> financial_pb2.FinancialReport:
    """Convert a financial_reports row dict to a proto FinancialReport message."""
    return financial_pb2.FinancialReport(
        symbol=symbol,
        report_date=str(row.get("report_date") or ""),
        report_type=str(row.get("report_type") or ""),
        revenue=_f(row, "revenue"),
        gross_profit=_f(row, "gross_profit"),
        operating_income=_f(row, "operating_income"),
        net_income=_f(row, "net_income"),
        eps=_f(row, "eps"),
        total_assets=_f(row, "total_assets"),
        total_liabilities=_f(row, "total_liabilities"),
        shareholders_equity=_f(row, "shareholders_equity"),
        book_value_per_share=_f(row, "book_value_per_share"),
        operating_cash_flow=_f(row, "operating_cash_flow"),
        free_cash_flow=_f(row, "free_cash_flow"),
        capex=_f(row, "capex"),
        shares_outstanding=_i(row, "shares_outstanding"),
        debt_to_equity=_f(row, "debt_to_equity"),
        current_ratio=_f(row, "current_ratio"),
        roe=_f(row, "roe"),
        roa=_f(row, "roa"),
    )
