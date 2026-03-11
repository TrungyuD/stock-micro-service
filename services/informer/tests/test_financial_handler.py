"""Tests for handlers/financial_handler.py — FinancialService RPCs with v1 proto types."""
from unittest.mock import MagicMock

import grpc
import pytest

from handlers.financial_handler import FinancialHandler, _dict_to_financial_report
from generated.informer.v1 import financial_pb2


@pytest.fixture
def mock_provider():
    return MagicMock()


@pytest.fixture
def mock_stock_repo():
    return MagicMock()


@pytest.fixture
def mock_financial_repo():
    return MagicMock()


@pytest.fixture
def financial_handler(mock_provider, mock_stock_repo, mock_financial_repo):
    return FinancialHandler(mock_provider, mock_stock_repo, mock_financial_repo)


def _make_financial_request(symbol="AAPL", period="Annual", years_back=5):
    """Build a mock GetFinancialRequest."""
    req = MagicMock()
    req.symbol = symbol
    req.period = period
    req.years_back = years_back
    return req


# ─── _dict_to_financial_report helper ────────────────────────────────────────

class TestDictToFinancialReport:
    def test_full_report_maps_all_fields(self, sample_financial_report):
        proto = _dict_to_financial_report(sample_financial_report, "AAPL")

        assert proto.symbol == "AAPL"
        assert proto.revenue == 394328000000
        assert proto.eps == 6.42
        assert proto.net_income == 96995000000
        assert proto.free_cash_flow == 107582000000

    def test_missing_fields_default_to_zero(self):
        proto = _dict_to_financial_report({}, "TEST")

        assert proto.symbol == "TEST"
        assert proto.revenue == 0.0
        assert proto.eps == 0.0
        assert proto.shares_outstanding == 0


# ─── GetIncomeStatement ───────────────────────────────────────────────────────

class TestGetIncomeStatement:
    def test_returns_income_statements_from_db(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_grpc_context, sample_financial_report
    ):
        mock_stock_repo.get_by_symbol.return_value = {"id": 1, "symbol": "AAPL"}
        mock_financial_repo.get_history.return_value = [sample_financial_report]
        request = _make_financial_request()

        resp = financial_handler.GetIncomeStatement(request, mock_grpc_context)

        assert resp.symbol == "AAPL"
        assert len(resp.statements) == 1
        assert resp.statements[0].revenue == 394328000000
        mock_grpc_context.set_code.assert_not_called()

    def test_falls_back_to_provider_on_db_miss(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_provider, mock_grpc_context, sample_financial_report
    ):
        mock_stock_repo.get_by_symbol.return_value = None
        mock_provider.get_financial_reports.return_value = [
            {**sample_financial_report, "report_type": "Annual"}
        ]
        request = _make_financial_request()

        resp = financial_handler.GetIncomeStatement(request, mock_grpc_context)

        assert resp.symbol == "AAPL"
        assert len(resp.statements) == 1
        mock_provider.get_financial_reports.assert_called_once_with("AAPL")

    def test_invalid_symbol_returns_invalid_argument(
        self, financial_handler, mock_grpc_context
    ):
        request = _make_financial_request(symbol="!!!")

        financial_handler.GetIncomeStatement(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_repo_error_returns_internal(
        self, financial_handler, mock_stock_repo, mock_grpc_context
    ):
        mock_stock_repo.get_by_symbol.side_effect = RuntimeError("db down")
        request = _make_financial_request()

        financial_handler.GetIncomeStatement(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


# ─── GetBalanceSheet ──────────────────────────────────────────────────────────

class TestGetBalanceSheet:
    def test_returns_balance_sheets_from_db(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_grpc_context, sample_financial_report
    ):
        mock_stock_repo.get_by_symbol.return_value = {"id": 1, "symbol": "AAPL"}
        mock_financial_repo.get_history.return_value = [sample_financial_report]
        request = _make_financial_request()

        resp = financial_handler.GetBalanceSheet(request, mock_grpc_context)

        assert resp.symbol == "AAPL"
        assert len(resp.sheets) == 1
        assert resp.sheets[0].total_assets == 352583000000
        mock_grpc_context.set_code.assert_not_called()

    def test_invalid_symbol_returns_invalid_argument(
        self, financial_handler, mock_grpc_context
    ):
        request = _make_financial_request(symbol="@BAD")

        financial_handler.GetBalanceSheet(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)


# ─── GetCashFlow ──────────────────────────────────────────────────────────────

class TestGetCashFlow:
    def test_returns_cash_flow_statements_from_db(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_grpc_context, sample_financial_report
    ):
        mock_stock_repo.get_by_symbol.return_value = {"id": 1, "symbol": "AAPL"}
        mock_financial_repo.get_history.return_value = [sample_financial_report]
        request = _make_financial_request()

        resp = financial_handler.GetCashFlow(request, mock_grpc_context)

        assert resp.symbol == "AAPL"
        assert len(resp.flows) == 1
        assert resp.flows[0].operating_cash_flow == 118254000000
        assert resp.flows[0].free_cash_flow == 107582000000
        mock_grpc_context.set_code.assert_not_called()

    def test_invalid_symbol_returns_invalid_argument(
        self, financial_handler, mock_grpc_context
    ):
        request = _make_financial_request(symbol="")

        financial_handler.GetCashFlow(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)


# ─── GetFinancialSummary ──────────────────────────────────────────────────────

class TestGetFinancialSummary:
    def test_returns_summary_from_latest_report(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_grpc_context, sample_financial_report
    ):
        mock_stock_repo.get_by_symbol.return_value = {"id": 1, "symbol": "AAPL"}
        mock_financial_repo.get_history.return_value = [sample_financial_report]
        request = MagicMock()
        request.symbol = "AAPL"

        resp = financial_handler.GetFinancialSummary(request, mock_grpc_context)

        assert resp.summary.symbol == "AAPL"
        assert resp.summary.revenue == 394328000000
        assert resp.summary.net_income == 96995000000
        assert resp.summary.free_cash_flow == 107582000000
        mock_grpc_context.set_code.assert_not_called()

    def test_no_data_returns_not_found(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_provider, mock_grpc_context
    ):
        mock_stock_repo.get_by_symbol.return_value = None
        mock_provider.get_financial_reports.return_value = []
        request = MagicMock()
        request.symbol = "ZZZZ"

        financial_handler.GetFinancialSummary(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_invalid_symbol_returns_invalid_argument(
        self, financial_handler, mock_grpc_context
    ):
        request = MagicMock()
        request.symbol = "!!!"

        financial_handler.GetFinancialSummary(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)


# ─── GetFinancialReports (backward-compat) ────────────────────────────────────

class TestGetFinancialReports:
    def test_returns_full_reports_list(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_grpc_context, sample_financial_report
    ):
        mock_stock_repo.get_by_symbol.return_value = {"id": 1, "symbol": "AAPL"}
        mock_financial_repo.get_history.return_value = [sample_financial_report]
        request = financial_pb2.GetFinancialReportsRequest(
            symbol="AAPL", report_type="Annual", years_back=5
        )

        resp = financial_handler.GetFinancialReports(request, mock_grpc_context)

        assert len(resp.reports) == 1
        assert resp.reports[0].symbol == "AAPL"
        assert resp.reports[0].revenue == 394328000000
        mock_grpc_context.set_code.assert_not_called()

    def test_falls_back_to_provider(
        self, financial_handler, mock_stock_repo, mock_financial_repo,
        mock_provider, mock_grpc_context, sample_financial_report
    ):
        mock_stock_repo.get_by_symbol.return_value = None
        mock_provider.get_financial_reports.return_value = [
            {**sample_financial_report, "report_type": "Annual"}
        ]
        request = financial_pb2.GetFinancialReportsRequest(
            symbol="AAPL", report_type="Annual", years_back=5
        )

        resp = financial_handler.GetFinancialReports(request, mock_grpc_context)

        assert len(resp.reports) == 1
        mock_provider.get_financial_reports.assert_called_once_with("AAPL")

    def test_invalid_symbol_returns_invalid_argument(
        self, financial_handler, mock_grpc_context
    ):
        request = financial_pb2.GetFinancialReportsRequest(symbol="", report_type="Annual")

        financial_handler.GetFinancialReports(request, mock_grpc_context)

        mock_grpc_context.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)
