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

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'gross_profit' })
  grossProfit: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'operating_income' })
  operatingIncome: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'net_income' })
  netIncome: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  eps: number | null;

  // --- Balance Sheet ---
  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'total_assets' })
  totalAssets: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'total_liabilities' })
  totalLiabilities: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'shareholders_equity' })
  shareholdersEquity: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'book_value_per_share' })
  bookValuePerShare: number | null;

  // --- Cash Flow ---
  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'operating_cash_flow' })
  operatingCashFlow: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true, name: 'free_cash_flow' })
  freeCashFlow: number | null;

  @Column({ type: 'decimal', precision: 18, scale: 2, nullable: true })
  capex: number | null;

  // --- Key Metrics ---
  @Column({ type: 'bigint', nullable: true, name: 'shares_outstanding' })
  sharesOutstanding: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'debt_to_equity' })
  debtToEquity: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'current_ratio' })
  currentRatio: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  roe: number | null;

  @Column({ type: 'decimal', precision: 10, scale: 4, nullable: true })
  roa: number | null;

  @CreateDateColumn({ type: 'timestamptz', name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ type: 'timestamptz', name: 'updated_at' })
  updatedAt: Date;

  @ManyToOne(() => StockEntity, (stock) => stock.financialReports, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'stock_id' })
  stock: StockEntity;
}
