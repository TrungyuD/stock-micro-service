from generated.common import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetStockInfoRequest(_message.Message):
    __slots__ = ("symbol",)
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    def __init__(self, symbol: _Optional[str] = ...) -> None: ...

class GetStockInfoResponse(_message.Message):
    __slots__ = ("stock",)
    STOCK_FIELD_NUMBER: _ClassVar[int]
    stock: _types_pb2.Stock
    def __init__(self, stock: _Optional[_Union[_types_pb2.Stock, _Mapping]] = ...) -> None: ...

class ListStocksRequest(_message.Message):
    __slots__ = ("exchange", "sector", "search", "pagination")
    EXCHANGE_FIELD_NUMBER: _ClassVar[int]
    SECTOR_FIELD_NUMBER: _ClassVar[int]
    SEARCH_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    exchange: str
    sector: str
    search: str
    pagination: _types_pb2.PaginationRequest
    def __init__(self, exchange: _Optional[str] = ..., sector: _Optional[str] = ..., search: _Optional[str] = ..., pagination: _Optional[_Union[_types_pb2.PaginationRequest, _Mapping]] = ...) -> None: ...

class ListStocksResponse(_message.Message):
    __slots__ = ("stocks", "pagination")
    STOCKS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    stocks: _containers.RepeatedCompositeFieldContainer[_types_pb2.Stock]
    pagination: _types_pb2.PaginationResponse
    def __init__(self, stocks: _Optional[_Iterable[_Union[_types_pb2.Stock, _Mapping]]] = ..., pagination: _Optional[_Union[_types_pb2.PaginationResponse, _Mapping]] = ...) -> None: ...

class BatchGetStocksRequest(_message.Message):
    __slots__ = ("symbols",)
    SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    symbols: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, symbols: _Optional[_Iterable[str]] = ...) -> None: ...

class BatchGetStocksResponse(_message.Message):
    __slots__ = ("stocks", "not_found")
    STOCKS_FIELD_NUMBER: _ClassVar[int]
    NOT_FOUND_FIELD_NUMBER: _ClassVar[int]
    stocks: _containers.RepeatedCompositeFieldContainer[_types_pb2.Stock]
    not_found: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, stocks: _Optional[_Iterable[_Union[_types_pb2.Stock, _Mapping]]] = ..., not_found: _Optional[_Iterable[str]] = ...) -> None: ...

class GetPriceHistoryRequest(_message.Message):
    __slots__ = ("symbol", "interval", "start_date", "end_date", "limit")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    END_DATE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    interval: str
    start_date: str
    end_date: str
    limit: int
    def __init__(self, symbol: _Optional[str] = ..., interval: _Optional[str] = ..., start_date: _Optional[str] = ..., end_date: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...

class GetPriceHistoryResponse(_message.Message):
    __slots__ = ("symbol", "candles", "total_records", "period_start", "period_end")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    CANDLES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_RECORDS_FIELD_NUMBER: _ClassVar[int]
    PERIOD_START_FIELD_NUMBER: _ClassVar[int]
    PERIOD_END_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    candles: _containers.RepeatedCompositeFieldContainer[_types_pb2.OHLCV]
    total_records: int
    period_start: str
    period_end: str
    def __init__(self, symbol: _Optional[str] = ..., candles: _Optional[_Iterable[_Union[_types_pb2.OHLCV, _Mapping]]] = ..., total_records: _Optional[int] = ..., period_start: _Optional[str] = ..., period_end: _Optional[str] = ...) -> None: ...

class FinancialReport(_message.Message):
    __slots__ = ("symbol", "report_date", "report_type", "revenue", "gross_profit", "operating_income", "net_income", "eps", "total_assets", "total_liabilities", "shareholders_equity", "book_value_per_share", "operating_cash_flow", "free_cash_flow", "capex", "shares_outstanding", "debt_to_equity", "current_ratio", "roe", "roa")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    REPORT_DATE_FIELD_NUMBER: _ClassVar[int]
    REPORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    REVENUE_FIELD_NUMBER: _ClassVar[int]
    GROSS_PROFIT_FIELD_NUMBER: _ClassVar[int]
    OPERATING_INCOME_FIELD_NUMBER: _ClassVar[int]
    NET_INCOME_FIELD_NUMBER: _ClassVar[int]
    EPS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ASSETS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_LIABILITIES_FIELD_NUMBER: _ClassVar[int]
    SHAREHOLDERS_EQUITY_FIELD_NUMBER: _ClassVar[int]
    BOOK_VALUE_PER_SHARE_FIELD_NUMBER: _ClassVar[int]
    OPERATING_CASH_FLOW_FIELD_NUMBER: _ClassVar[int]
    FREE_CASH_FLOW_FIELD_NUMBER: _ClassVar[int]
    CAPEX_FIELD_NUMBER: _ClassVar[int]
    SHARES_OUTSTANDING_FIELD_NUMBER: _ClassVar[int]
    DEBT_TO_EQUITY_FIELD_NUMBER: _ClassVar[int]
    CURRENT_RATIO_FIELD_NUMBER: _ClassVar[int]
    ROE_FIELD_NUMBER: _ClassVar[int]
    ROA_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    report_date: str
    report_type: str
    revenue: float
    gross_profit: float
    operating_income: float
    net_income: float
    eps: float
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    book_value_per_share: float
    operating_cash_flow: float
    free_cash_flow: float
    capex: float
    shares_outstanding: int
    debt_to_equity: float
    current_ratio: float
    roe: float
    roa: float
    def __init__(self, symbol: _Optional[str] = ..., report_date: _Optional[str] = ..., report_type: _Optional[str] = ..., revenue: _Optional[float] = ..., gross_profit: _Optional[float] = ..., operating_income: _Optional[float] = ..., net_income: _Optional[float] = ..., eps: _Optional[float] = ..., total_assets: _Optional[float] = ..., total_liabilities: _Optional[float] = ..., shareholders_equity: _Optional[float] = ..., book_value_per_share: _Optional[float] = ..., operating_cash_flow: _Optional[float] = ..., free_cash_flow: _Optional[float] = ..., capex: _Optional[float] = ..., shares_outstanding: _Optional[int] = ..., debt_to_equity: _Optional[float] = ..., current_ratio: _Optional[float] = ..., roe: _Optional[float] = ..., roa: _Optional[float] = ...) -> None: ...

class GetFinancialReportRequest(_message.Message):
    __slots__ = ("symbol", "report_type")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    REPORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    report_type: str
    def __init__(self, symbol: _Optional[str] = ..., report_type: _Optional[str] = ...) -> None: ...

class GetFinancialReportResponse(_message.Message):
    __slots__ = ("report",)
    REPORT_FIELD_NUMBER: _ClassVar[int]
    report: FinancialReport
    def __init__(self, report: _Optional[_Union[FinancialReport, _Mapping]] = ...) -> None: ...

class GetFinancialReportsRequest(_message.Message):
    __slots__ = ("symbol", "report_type", "years_back")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    REPORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    YEARS_BACK_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    report_type: str
    years_back: int
    def __init__(self, symbol: _Optional[str] = ..., report_type: _Optional[str] = ..., years_back: _Optional[int] = ...) -> None: ...

class GetFinancialReportsResponse(_message.Message):
    __slots__ = ("reports",)
    REPORTS_FIELD_NUMBER: _ClassVar[int]
    reports: _containers.RepeatedCompositeFieldContainer[FinancialReport]
    def __init__(self, reports: _Optional[_Iterable[_Union[FinancialReport, _Mapping]]] = ...) -> None: ...

class TriggerDataCollectionRequest(_message.Message):
    __slots__ = ("symbols", "data_type", "start_date")
    SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    symbols: _containers.RepeatedScalarFieldContainer[str]
    data_type: str
    start_date: str
    def __init__(self, symbols: _Optional[_Iterable[str]] = ..., data_type: _Optional[str] = ..., start_date: _Optional[str] = ...) -> None: ...

class TriggerDataCollectionResponse(_message.Message):
    __slots__ = ("accepted", "job_id", "message")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    job_id: str
    message: str
    def __init__(self, accepted: bool = ..., job_id: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "version", "uptime")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    status: str
    version: str
    uptime: str
    def __init__(self, status: _Optional[str] = ..., version: _Optional[str] = ..., uptime: _Optional[str] = ...) -> None: ...
