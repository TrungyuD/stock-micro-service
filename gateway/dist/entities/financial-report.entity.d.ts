import { StockEntity } from './stock.entity';
export declare class FinancialReportEntity {
    id: number;
    stockId: number;
    reportDate: Date;
    reportType: 'Annual' | 'Quarterly';
    revenue: number | null;
    grossProfit: number | null;
    operatingIncome: number | null;
    netIncome: number | null;
    eps: number | null;
    totalAssets: number | null;
    totalLiabilities: number | null;
    shareholdersEquity: number | null;
    bookValuePerShare: number | null;
    operatingCashFlow: number | null;
    freeCashFlow: number | null;
    capex: number | null;
    sharesOutstanding: number | null;
    debtToEquity: number | null;
    currentRatio: number | null;
    roe: number | null;
    roa: number | null;
    createdAt: Date;
    updatedAt: Date;
    stock: StockEntity;
}
