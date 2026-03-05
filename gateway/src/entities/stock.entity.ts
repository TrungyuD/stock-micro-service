/**
 * stock.entity.ts — TypeORM entity for the `stocks` table.
 * Stores stock metadata: symbol, name, sector, exchange, etc.
 */
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
  OneToMany,
} from 'typeorm';
import { OhlcvEntity } from './ohlcv.entity';
import { FinancialReportEntity } from './financial-report.entity';
import { IndicatorEntity } from './indicator.entity';
import { ValuationMetricEntity } from './valuation-metric.entity';
import { WatchlistItemEntity } from './watchlist-item.entity';

@Entity('stocks')
@Index('idx_stocks_sector', ['sector'])
@Index('idx_stocks_exchange', ['exchange'])
export class StockEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'varchar', length: 10, unique: true })
  @Index('idx_stocks_symbol')
  symbol: string;

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'varchar', length: 100, nullable: true })
  sector: string | null;

  @Column({ type: 'varchar', length: 100, nullable: true })
  industry: string | null;

  @Column({ type: 'varchar', length: 50, nullable: true })
  exchange: string | null;

  @Column({ type: 'varchar', length: 50, default: 'US' })
  country: string;

  @Column({ type: 'varchar', length: 10, default: 'USD' })
  currency: string;

  @Column({ type: 'bigint', nullable: true })
  marketCap: number | null;

  @Column({ type: 'text', nullable: true })
  description: string | null;

  @Column({ type: 'varchar', length: 255, nullable: true })
  website: string | null;

  @Column({ type: 'boolean', default: true })
  isActive: boolean;

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ type: 'timestamptz' })
  updatedAt: Date;

  // Relations
  @OneToMany(() => OhlcvEntity, (ohlcv) => ohlcv.stock)
  ohlcv: OhlcvEntity[];

  @OneToMany(() => FinancialReportEntity, (report) => report.stock)
  financialReports: FinancialReportEntity[];

  @OneToMany(() => IndicatorEntity, (indicator) => indicator.stock)
  indicators: IndicatorEntity[];

  @OneToMany(() => ValuationMetricEntity, (metric) => metric.stock)
  valuationMetrics: ValuationMetricEntity[];

  @OneToMany(() => WatchlistItemEntity, (item) => item.stock)
  watchlistItems: WatchlistItemEntity[];
}
