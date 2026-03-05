/**
 * watchlist-item.entity.ts — TypeORM entity for the `watchlist_items` join table.
 * Resolves the many-to-many relationship between watchlists and stocks.
 */
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
  Index,
  Unique,
} from 'typeorm';
import { WatchlistEntity } from './watchlist.entity';
import { StockEntity } from './stock.entity';

@Entity('watchlist_items')
@Unique(['watchlistId', 'stockId'])
@Index('idx_watchlist_items_watchlist', ['watchlistId'])
export class WatchlistItemEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'watchlist_id' })
  watchlistId: number;

  @Column({ name: 'stock_id' })
  stockId: number;

  @CreateDateColumn({ type: 'timestamptz', name: 'added_at' })
  addedAt: Date;

  @ManyToOne(() => WatchlistEntity, (watchlist) => watchlist.items, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'watchlist_id' })
  watchlist: WatchlistEntity;

  @ManyToOne(() => StockEntity, (stock) => stock.watchlistItems, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'stock_id' })
  stock: StockEntity;
}
