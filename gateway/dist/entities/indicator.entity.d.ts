import { StockEntity } from './stock.entity';
export declare class IndicatorEntity {
    id: number;
    stockId: number;
    time: Date;
    rsi14: number | null;
    sma20: number | null;
    sma50: number | null;
    sma200: number | null;
    ema20: number | null;
    ema50: number | null;
    macdLine: number | null;
    macdSignal: number | null;
    macdHistogram: number | null;
    bbUpper: number | null;
    bbMiddle: number | null;
    bbLower: number | null;
    createdAt: Date;
    stock: StockEntity;
}
