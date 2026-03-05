import { WatchlistItemEntity } from './watchlist-item.entity';
export declare class WatchlistEntity {
    id: number;
    userId: string;
    name: string;
    createdAt: Date;
    updatedAt: Date;
    items: WatchlistItemEntity[];
}
