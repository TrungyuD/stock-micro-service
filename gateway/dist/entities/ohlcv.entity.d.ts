import { StockEntity } from './stock.entity';
export declare class OhlcvEntity {
    time: Date;
    stockId: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    adjustedClose: number | null;
    stock: StockEntity;
}
