"""
base_provider.py — Abstract base class for stock data providers.
All concrete providers (yfinance, Alpha Vantage) must implement this interface.
"""
from abc import ABC, abstractmethod

import pandas as pd


class BaseProvider(ABC):
    """
    Contract for stock data sources.

    Each provider must be able to supply:
      - Stock metadata (name, sector, market cap, etc.)
      - Historical OHLCV data as a pandas DataFrame
      - Financial reports (income statement, balance sheet, cash flow)
    """

    @abstractmethod
    def get_stock_metadata(self, symbol: str) -> dict:
        """
        Fetch static/slowly-changing information about a stock.

        Returns:
            dict with keys: symbol, name, sector, industry, exchange,
            country, currency, market_cap, description, website.
        """
        ...

    @abstractmethod
    def get_historical_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV data for a symbol between two ISO dates.

        Args:
            symbol:     Ticker, e.g. 'AAPL'.
            start_date: ISO 'YYYY-MM-DD' (inclusive).
            end_date:   ISO 'YYYY-MM-DD' (inclusive).

        Returns:
            DataFrame with columns: time, open, high, low, close,
            volume, adjusted_close.  Empty DataFrame on failure.
        """
        ...

    @abstractmethod
    def get_financial_reports(self, symbol: str) -> list[dict]:
        """
        Fetch available financial reports (income stmt, balance sheet, cash flow).

        Returns:
            List of dicts, each matching `financial_reports` schema columns:
            report_date, report_type ('Annual'|'Quarterly'), revenue,
            gross_profit, operating_income, net_income, eps, total_assets,
            total_liabilities, shareholders_equity, book_value_per_share,
            operating_cash_flow, free_cash_flow, capex,
            shares_outstanding, debt_to_equity, current_ratio, roe, roa.
        """
        ...
