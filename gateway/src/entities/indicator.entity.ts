/**
 * indicator.entity.ts — TypeORM entity for the `indicators` table.
 * Caches computed technical indicators (RSI, MACD, Bollinger Bands, MAs)
 * to avoid re-running expensive rolling-window calculations.
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

@Entity('indicators')
@Unique(['stockId', 'time'])
@Index('idx_indicators_stock_time', ['stockId', 'time'])
export class IndicatorEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'stock_id' })
  stockId: number;

  @Column({ type: 'timestamptz' })
  time: Date;

  // --- RSI ---
  @Column({ type: 'decimal', precision: 6, scale: 2, nullable: true, name: 'rsi_14' })
  rsi14: number | null;

  // --- Simple Moving Averages ---
  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'sma_20' })
  sma20: number | null;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'sma_50' })
  sma50: number | null;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'sma_200' })
  sma200: number | null;

  // --- Exponential Moving Averages ---
  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'ema_20' })
  ema20: number | null;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'ema_50' })
  ema50: number | null;

  // --- MACD (12/26/9) ---
  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'macd_line' })
  macdLine: number | null;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'macd_signal' })
  macdSignal: number | null;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'macd_histogram' })
  macdHistogram: number | null;

  // --- Bollinger Bands (20-period, 2 std dev) ---
  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'bb_upper' })
  bbUpper: number | null;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'bb_middle' })
  bbMiddle: number | null;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'bb_lower' })
  bbLower: number | null;

  @CreateDateColumn({ type: 'timestamptz', name: 'created_at' })
  createdAt: Date;

  @ManyToOne(() => StockEntity, (stock) => stock.indicators, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'stock_id' })
  stock: StockEntity;
}
