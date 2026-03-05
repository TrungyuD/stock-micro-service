import { WatchlistEntity } from './watchlist.entity';
import { StockEntity } from './stock.entity';
export declare class WatchlistItemEntity {
    id: number;
    watchlistId: number;
    stockId: number;
    addedAt: Date;
    watchlist: WatchlistEntity;
    stock: StockEntity;
}
