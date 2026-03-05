import { StockEntity } from './stock.entity';
export declare class ValuationMetricEntity {
    id: number;
    stockId: number;
    calculatedAt: Date;
    trailingPe: number | null;
    forwardPe: number | null;
    priceToBook: number | null;
    pegRatio: number | null;
    priceToSales: number | null;
    evToEbitda: number | null;
    dividendYield: number | null;
    payoutRatio: number | null;
    valuationSignal: string | null;
    valuationScore: number | null;
    createdAt: Date;
    stock: StockEntity;
}
