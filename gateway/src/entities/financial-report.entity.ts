/**
 * financial-report.entity.ts — TypeORM entity for the `financial_reports` table.
 * Stores quarterly/annual income statement, balance sheet, and cash flow data.
 */
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
  Unique,
} from 'typeorm';
import { StockEntity } from './stock.entity';

@Entity('financial_reports')
@Unique(['stockId', 'reportDate', 'reportType'])
@Index('idx_financial_reports_stock', ['stockId', 'reportDate'])
export class FinancialReportEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'stock_id' })
  stockId: number;

  @Column({ type: 'date', name: 'report_date' })
  reportDate: Date;

  /** 'Annual' or 'Quarterly' — enforced by CHECK constraint in DDL */
  @Column({ type: 'varchar', length: 20, name: 'report_type' })
  reportType: 'Annual' | 'Quarterly';

  // --- Income Statement ---
  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  revenue: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  grossProfit: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  operatingIncome: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  netIncome: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  eps: number | null;

  // --- Balance Sheet ---
  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  totalAssets: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  totalLiabilities: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  shareholdersEquity: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  bookValuePerShare: number | null;

  // --- Cash Flow ---
  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  operatingCashFlow: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  freeCashFlow: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  capex: number | null;

  // --- Key Metrics ---
  @Column({ type: 'bigint', nullable: true })
  sharesOutstanding: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  debtToEquity: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  currentRatio: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  roe: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  roa: number | null;

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ type: 'timestamptz' })
  updatedAt: Date;

  @ManyToOne(() => StockEntity, (stock) => stock.financialReports, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'stock_id' })
  stock: StockEntity;
}
