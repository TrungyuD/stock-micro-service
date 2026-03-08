/**
 * ohlcv.entity.ts — TypeORM entity for the `ohlcv` TimescaleDB hypertable.
 * Stores daily Open/High/Low/Close/Volume price data per stock.
 * NOTE: `time` is the hypertable partition key — do NOT use @PrimaryGeneratedColumn here.
 */
import {
  Entity,
  Column,
  ManyToOne,
  JoinColumn,
  Index,
  PrimaryColumn,
} from 'typeorm';
import { StockEntity } from './stock.entity';

@Entity('ohlcv')
@Index('idx_ohlcv_stock_time', ['stockId', 'time'])
export class OhlcvEntity {
  /**
   * TimescaleDB hypertable partition key.
   * Composite primary key: (stock_id, time) — matches the UNIQUE constraint in DDL.
   */
  @PrimaryColumn({ type: 'timestamptz', name: 'time' })
  time: Date;

  @PrimaryColumn({ type: 'integer', name: 'stock_id' })
  stockId: number;

  @Column({ type: 'decimal', precision: 12, scale: 4 })
  open: number;

  @Column({ type: 'decimal', precision: 12, scale: 4 })
  high: number;

  @Column({ type: 'decimal', precision: 12, scale: 4 })
  low: number;

  @Column({ type: 'decimal', precision: 12, scale: 4 })
  close: number;

  @Column({ type: 'bigint' })
  volume: number;

  @Column({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'adjusted_close' })
  adjustedClose: number | null;

  // Relation — not loaded by default (use QueryBuilder when needed)
  @ManyToOne(() => StockEntity, (stock) => stock.ohlcv, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'stock_id' })
  stock: StockEntity;
}
