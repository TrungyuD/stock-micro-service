import { OhlcvEntity } from './ohlcv.entity';
import { FinancialReportEntity } from './financial-report.entity';
import { IndicatorEntity } from './indicator.entity';
import { ValuationMetricEntity } from './valuation-metric.entity';
import { WatchlistItemEntity } from './watchlist-item.entity';
export declare class StockEntity {
    id: number;
    symbol: string;
    name: string;
    sector: string | null;
    industry: string | null;
    exchange: string | null;
    country: string;
    currency: string;
    marketCap: number | null;
    description: string | null;
    website: string | null;
    isActive: boolean;
    createdAt: Date;
    updatedAt: Date;
    ohlcv: OhlcvEntity[];
    financialReports: FinancialReportEntity[];
    indicators: IndicatorEntity[];
    valuationMetrics: ValuationMetricEntity[];
    watchlistItems: WatchlistItemEntity[];
}
