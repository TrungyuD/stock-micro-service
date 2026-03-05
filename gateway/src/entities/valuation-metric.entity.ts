/**
 * valuation-metric.entity.ts — TypeORM entity for the `valuation_metrics` table.
 * Caches fundamental valuation ratios (P/E, P/B, EV/EBITDA, etc.) per stock snapshot.
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
import { StockEntity } from './stock.entity';

@Entity('valuation_metrics')
@Unique(['stockId', 'calculatedAt'])
@Index('idx_valuation_stock', ['stockId', 'calculatedAt'])
export class ValuationMetricEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'stock_id' })
  stockId: number;

  @Column({ type: 'timestamptz', name: 'calculated_at', default: () => 'NOW()' })
  calculatedAt: Date;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'trailing_pe' })
  trailingPe: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'forward_pe' })
  forwardPe: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'price_to_book' })
  priceToBook: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'peg_ratio' })
  pegRatio: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'price_to_sales' })
  priceToSales: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'ev_to_ebitda' })
  evToEbitda: number | null;

  @Column({ type: 'decimal', precision: 8, scale: 4, nullable: true, name: 'dividend_yield' })
  dividendYield: number | null;

  @Column({ type: 'decimal', precision: 8, scale: 4, nullable: true, name: 'payout_ratio' })
  payoutRatio: number | null;

  /** Computed signal: 'Undervalued' | 'Fair Value' | 'Overvalued' */
  @Column({ type: 'varchar', length: 20, nullable: true, name: 'valuation_signal' })
  valuationSignal: string | null;

  @Column({ type: 'decimal', precision: 5, scale: 2, nullable: true, name: 'valuation_score' })
  valuationScore: number | null;

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;

  @ManyToOne(() => StockEntity, (stock) => stock.valuationMetrics, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'stock_id' })
  stock: StockEntity;
}
