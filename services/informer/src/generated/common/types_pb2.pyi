from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Stock(_message.Message):
    __slots__ = ("id", "symbol", "name", "sector", "industry", "exchange", "country", "currency", "market_cap", "description", "website", "is_active")
    ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SECTOR_FIELD_NUMBER: _ClassVar[int]
    INDUSTRY_FIELD_NUMBER: _ClassVar[int]
    EXCHANGE_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    MARKET_CAP_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    WEBSITE_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    id: int
    symbol: str
    name: str
    sector: str
    industry: str
    exchange: str
    country: str
    currency: str
    market_cap: int
    description: str
    website: str
    is_active: bool
    def __init__(self, id: _Optional[int] = ..., symbol: _Optional[str] = ..., name: _Optional[str] = ..., sector: _Optional[str] = ..., industry: _Optional[str] = ..., exchange: _Optional[str] = ..., country: _Optional[str] = ..., currency: _Optional[str] = ..., market_cap: _Optional[int] = ..., description: _Optional[str] = ..., website: _Optional[str] = ..., is_active: bool = ...) -> None: ...

class OHLCV(_message.Message):
    __slots__ = ("date", "open", "high", "low", "close", "volume", "adjusted_close")
    DATE_FIELD_NUMBER: _ClassVar[int]
    OPEN_FIELD_NUMBER: _ClassVar[int]
    HIGH_FIELD_NUMBER: _ClassVar[int]
    LOW_FIELD_NUMBER: _ClassVar[int]
    CLOSE_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    ADJUSTED_CLOSE_FIELD_NUMBER: _ClassVar[int]
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: float
    def __init__(self, date: _Optional[str] = ..., open: _Optional[float] = ..., high: _Optional[float] = ..., low: _Optional[float] = ..., close: _Optional[float] = ..., volume: _Optional[int] = ..., adjusted_close: _Optional[float] = ...) -> None: ...

class PaginationRequest(_message.Message):
    __slots__ = ("page", "page_size")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    page: int
    page_size: int
    def __init__(self, page: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class PaginationResponse(_message.Message):
    __slots__ = ("total_count", "page", "page_size", "total_pages")
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PAGES_FIELD_NUMBER: _ClassVar[int]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    def __init__(self, total_count: _Optional[int] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ..., total_pages: _Optional[int] = ...) -> None: ...

class StatusResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
