from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ValuationMetrics(_message.Message):
    __slots__ = ("symbol", "trailing_pe", "forward_pe", "current_eps", "price_to_book", "book_value_per_share", "peg_ratio", "earnings_growth_rate", "dividend_yield", "payout_ratio", "price_to_sales", "ev_to_ebitda", "valuation_signal", "valuation_score", "calculated_at")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    TRAILING_PE_FIELD_NUMBER: _ClassVar[int]
    FORWARD_PE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_EPS_FIELD_NUMBER: _ClassVar[int]
    PRICE_TO_BOOK_FIELD_NUMBER: _ClassVar[int]
    BOOK_VALUE_PER_SHARE_FIELD_NUMBER: _ClassVar[int]
    PEG_RATIO_FIELD_NUMBER: _ClassVar[int]
    EARNINGS_GROWTH_RATE_FIELD_NUMBER: _ClassVar[int]
    DIVIDEND_YIELD_FIELD_NUMBER: _ClassVar[int]
    PAYOUT_RATIO_FIELD_NUMBER: _ClassVar[int]
    PRICE_TO_SALES_FIELD_NUMBER: _ClassVar[int]
    EV_TO_EBITDA_FIELD_NUMBER: _ClassVar[int]
    VALUATION_SIGNAL_FIELD_NUMBER: _ClassVar[int]
    VALUATION_SCORE_FIELD_NUMBER: _ClassVar[int]
    CALCULATED_AT_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    trailing_pe: float
    forward_pe: float
    current_eps: float
    price_to_book: float
    book_value_per_share: float
    peg_ratio: float
    earnings_growth_rate: float
    dividend_yield: float
    payout_ratio: float
    price_to_sales: float
    ev_to_ebitda: float
    valuation_signal: str
    valuation_score: float
    calculated_at: str
    def __init__(self, symbol: _Optional[str] = ..., trailing_pe: _Optional[float] = ..., forward_pe: _Optional[float] = ..., current_eps: _Optional[float] = ..., price_to_book: _Optional[float] = ..., book_value_per_share: _Optional[float] = ..., peg_ratio: _Optional[float] = ..., earnings_growth_rate: _Optional[float] = ..., dividend_yield: _Optional[float] = ..., payout_ratio: _Optional[float] = ..., price_to_sales: _Optional[float] = ..., ev_to_ebitda: _Optional[float] = ..., valuation_signal: _Optional[str] = ..., valuation_score: _Optional[float] = ..., calculated_at: _Optional[str] = ...) -> None: ...

class GetValuationMetricsRequest(_message.Message):
    __slots__ = ("symbol",)
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    def __init__(self, symbol: _Optional[str] = ...) -> None: ...

class GetValuationMetricsResponse(_message.Message):
    __slots__ = ("metrics",)
    METRICS_FIELD_NUMBER: _ClassVar[int]
    metrics: ValuationMetrics
    def __init__(self, metrics: _Optional[_Union[ValuationMetrics, _Mapping]] = ...) -> None: ...

class RSI(_message.Message):
    __slots__ = ("period", "value", "signal")
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_FIELD_NUMBER: _ClassVar[int]
    period: int
    value: float
    signal: str
    def __init__(self, period: _Optional[int] = ..., value: _Optional[float] = ..., signal: _Optional[str] = ...) -> None: ...

class MovingAverages(_message.Message):
    __slots__ = ("sma_20", "sma_50", "sma_200", "ema_20", "ema_50", "trend_signal")
    SMA_20_FIELD_NUMBER: _ClassVar[int]
    SMA_50_FIELD_NUMBER: _ClassVar[int]
    SMA_200_FIELD_NUMBER: _ClassVar[int]
    EMA_20_FIELD_NUMBER: _ClassVar[int]
    EMA_50_FIELD_NUMBER: _ClassVar[int]
    TREND_SIGNAL_FIELD_NUMBER: _ClassVar[int]
    sma_20: float
    sma_50: float
    sma_200: float
    ema_20: float
    ema_50: float
    trend_signal: str
    def __init__(self, sma_20: _Optional[float] = ..., sma_50: _Optional[float] = ..., sma_200: _Optional[float] = ..., ema_20: _Optional[float] = ..., ema_50: _Optional[float] = ..., trend_signal: _Optional[str] = ...) -> None: ...

class MACDIndicator(_message.Message):
    __slots__ = ("macd_line", "signal_line", "histogram", "signal")
    MACD_LINE_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_LINE_FIELD_NUMBER: _ClassVar[int]
    HISTOGRAM_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_FIELD_NUMBER: _ClassVar[int]
    macd_line: float
    signal_line: float
    histogram: float
    signal: str
    def __init__(self, macd_line: _Optional[float] = ..., signal_line: _Optional[float] = ..., histogram: _Optional[float] = ..., signal: _Optional[str] = ...) -> None: ...

class BollingerBands(_message.Message):
    __slots__ = ("upper_band", "middle_band", "lower_band", "band_width", "percent_b")
    UPPER_BAND_FIELD_NUMBER: _ClassVar[int]
    MIDDLE_BAND_FIELD_NUMBER: _ClassVar[int]
    LOWER_BAND_FIELD_NUMBER: _ClassVar[int]
    BAND_WIDTH_FIELD_NUMBER: _ClassVar[int]
    PERCENT_B_FIELD_NUMBER: _ClassVar[int]
    upper_band: float
    middle_band: float
    lower_band: float
    band_width: float
    percent_b: float
    def __init__(self, upper_band: _Optional[float] = ..., middle_band: _Optional[float] = ..., lower_band: _Optional[float] = ..., band_width: _Optional[float] = ..., percent_b: _Optional[float] = ...) -> None: ...

class TechnicalIndicators(_message.Message):
    __slots__ = ("symbol", "rsi", "moving_averages", "macd", "bollinger_bands", "overall_signal", "buy_signals", "sell_signals", "calculated_at")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    RSI_FIELD_NUMBER: _ClassVar[int]
    MOVING_AVERAGES_FIELD_NUMBER: _ClassVar[int]
    MACD_FIELD_NUMBER: _ClassVar[int]
    BOLLINGER_BANDS_FIELD_NUMBER: _ClassVar[int]
    OVERALL_SIGNAL_FIELD_NUMBER: _ClassVar[int]
    BUY_SIGNALS_FIELD_NUMBER: _ClassVar[int]
    SELL_SIGNALS_FIELD_NUMBER: _ClassVar[int]
    CALCULATED_AT_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    rsi: RSI
    moving_averages: MovingAverages
    macd: MACDIndicator
    bollinger_bands: BollingerBands
    overall_signal: str
    buy_signals: int
    sell_signals: int
    calculated_at: str
    def __init__(self, symbol: _Optional[str] = ..., rsi: _Optional[_Union[RSI, _Mapping]] = ..., moving_averages: _Optional[_Union[MovingAverages, _Mapping]] = ..., macd: _Optional[_Union[MACDIndicator, _Mapping]] = ..., bollinger_bands: _Optional[_Union[BollingerBands, _Mapping]] = ..., overall_signal: _Optional[str] = ..., buy_signals: _Optional[int] = ..., sell_signals: _Optional[int] = ..., calculated_at: _Optional[str] = ...) -> None: ...

class GetTechnicalIndicatorsRequest(_message.Message):
    __slots__ = ("symbol", "timeframe")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    TIMEFRAME_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    timeframe: str
    def __init__(self, symbol: _Optional[str] = ..., timeframe: _Optional[str] = ...) -> None: ...

class GetTechnicalIndicatorsResponse(_message.Message):
    __slots__ = ("indicators",)
    INDICATORS_FIELD_NUMBER: _ClassVar[int]
    indicators: TechnicalIndicators
    def __init__(self, indicators: _Optional[_Union[TechnicalIndicators, _Mapping]] = ...) -> None: ...

class StockAnalysis(_message.Message):
    __slots__ = ("symbol", "company_name", "current_price", "valuation", "technicals", "recommendation", "confidence_score", "rationale", "analysis_timestamp")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    COMPANY_NAME_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PRICE_FIELD_NUMBER: _ClassVar[int]
    VALUATION_FIELD_NUMBER: _ClassVar[int]
    TECHNICALS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_SCORE_FIELD_NUMBER: _ClassVar[int]
    RATIONALE_FIELD_NUMBER: _ClassVar[int]
    ANALYSIS_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    company_name: str
    current_price: float
    valuation: ValuationMetrics
    technicals: TechnicalIndicators
    recommendation: str
    confidence_score: float
    rationale: str
    analysis_timestamp: str
    def __init__(self, symbol: _Optional[str] = ..., company_name: _Optional[str] = ..., current_price: _Optional[float] = ..., valuation: _Optional[_Union[ValuationMetrics, _Mapping]] = ..., technicals: _Optional[_Union[TechnicalIndicators, _Mapping]] = ..., recommendation: _Optional[str] = ..., confidence_score: _Optional[float] = ..., rationale: _Optional[str] = ..., analysis_timestamp: _Optional[str] = ...) -> None: ...

class GetStockAnalysisRequest(_message.Message):
    __slots__ = ("symbol", "include_rationale")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_RATIONALE_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    include_rationale: bool
    def __init__(self, symbol: _Optional[str] = ..., include_rationale: bool = ...) -> None: ...

class GetStockAnalysisResponse(_message.Message):
    __slots__ = ("analysis",)
    ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    analysis: StockAnalysis
    def __init__(self, analysis: _Optional[_Union[StockAnalysis, _Mapping]] = ...) -> None: ...

class BatchAnalysisRequest(_message.Message):
    __slots__ = ("symbols",)
    SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    symbols: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, symbols: _Optional[_Iterable[str]] = ...) -> None: ...

class BatchAnalysisResponse(_message.Message):
    __slots__ = ("analyses", "failed_symbols")
    ANALYSES_FIELD_NUMBER: _ClassVar[int]
    FAILED_SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    analyses: _containers.RepeatedCompositeFieldContainer[StockAnalysis]
    failed_symbols: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, analyses: _Optional[_Iterable[_Union[StockAnalysis, _Mapping]]] = ..., failed_symbols: _Optional[_Iterable[str]] = ...) -> None: ...

class ScreeningCriteria(_message.Message):
    __slots__ = ("min_pe", "max_pe", "min_peg", "max_peg", "min_dividend_yield", "max_dividend_yield", "rsi_oversold", "rsi_overbought", "trend_direction", "sector")
    MIN_PE_FIELD_NUMBER: _ClassVar[int]
    MAX_PE_FIELD_NUMBER: _ClassVar[int]
    MIN_PEG_FIELD_NUMBER: _ClassVar[int]
    MAX_PEG_FIELD_NUMBER: _ClassVar[int]
    MIN_DIVIDEND_YIELD_FIELD_NUMBER: _ClassVar[int]
    MAX_DIVIDEND_YIELD_FIELD_NUMBER: _ClassVar[int]
    RSI_OVERSOLD_FIELD_NUMBER: _ClassVar[int]
    RSI_OVERBOUGHT_FIELD_NUMBER: _ClassVar[int]
    TREND_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    SECTOR_FIELD_NUMBER: _ClassVar[int]
    min_pe: float
    max_pe: float
    min_peg: float
    max_peg: float
    min_dividend_yield: float
    max_dividend_yield: float
    rsi_oversold: bool
    rsi_overbought: bool
    trend_direction: str
    sector: str
    def __init__(self, min_pe: _Optional[float] = ..., max_pe: _Optional[float] = ..., min_peg: _Optional[float] = ..., max_peg: _Optional[float] = ..., min_dividend_yield: _Optional[float] = ..., max_dividend_yield: _Optional[float] = ..., rsi_oversold: bool = ..., rsi_overbought: bool = ..., trend_direction: _Optional[str] = ..., sector: _Optional[str] = ...) -> None: ...

class ScreenStocksRequest(_message.Message):
    __slots__ = ("criteria", "limit", "sort_by")
    CRITERIA_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    SORT_BY_FIELD_NUMBER: _ClassVar[int]
    criteria: ScreeningCriteria
    limit: int
    sort_by: str
    def __init__(self, criteria: _Optional[_Union[ScreeningCriteria, _Mapping]] = ..., limit: _Optional[int] = ..., sort_by: _Optional[str] = ...) -> None: ...

class ScreenedStock(_message.Message):
    __slots__ = ("symbol", "company_name", "current_price", "match_score", "valuation", "technicals")
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    COMPANY_NAME_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PRICE_FIELD_NUMBER: _ClassVar[int]
    MATCH_SCORE_FIELD_NUMBER: _ClassVar[int]
    VALUATION_FIELD_NUMBER: _ClassVar[int]
    TECHNICALS_FIELD_NUMBER: _ClassVar[int]
    symbol: str
    company_name: str
    current_price: float
    match_score: float
    valuation: ValuationMetrics
    technicals: TechnicalIndicators
    def __init__(self, symbol: _Optional[str] = ..., company_name: _Optional[str] = ..., current_price: _Optional[float] = ..., match_score: _Optional[float] = ..., valuation: _Optional[_Union[ValuationMetrics, _Mapping]] = ..., technicals: _Optional[_Union[TechnicalIndicators, _Mapping]] = ...) -> None: ...

class ScreenStocksResponse(_message.Message):
    __slots__ = ("stocks", "total_matched")
    STOCKS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MATCHED_FIELD_NUMBER: _ClassVar[int]
    stocks: _containers.RepeatedCompositeFieldContainer[ScreenedStock]
    total_matched: int
    def __init__(self, stocks: _Optional[_Iterable[_Union[ScreenedStock, _Mapping]]] = ..., total_matched: _Optional[int] = ...) -> None: ...

class TriggerCalculationRequest(_message.Message):
    __slots__ = ("symbols", "calculation_type")
    SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    CALCULATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    symbols: _containers.RepeatedScalarFieldContainer[str]
    calculation_type: str
    def __init__(self, symbols: _Optional[_Iterable[str]] = ..., calculation_type: _Optional[str] = ...) -> None: ...

class TriggerCalculationResponse(_message.Message):
    __slots__ = ("accepted", "message")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    message: str
    def __init__(self, accepted: bool = ..., message: _Optional[str] = ...) -> None: ...

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
