/**
 * watchlists.module.ts — NestJS module for watchlist CRUD operations.
 * Uses TypeORM repositories for direct DB access (no gRPC needed).
 */
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { WatchlistsController } from './watchlists.controller';
import { WatchlistsService } from './watchlists.service';
import { WatchlistEntity } from '../entities/watchlist.entity';
import { WatchlistItemEntity } from '../entities/watchlist-item.entity';
import { StockEntity } from '../entities/stock.entity';
import { OhlcvEntity } from '../entities/ohlcv.entity';
import { FinancialReportEntity } from '../entities/financial-report.entity';
import { IndicatorEntity } from '../entities/indicator.entity';
import { ValuationMetricEntity } from '../entities/valuation-metric.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      WatchlistEntity,
      WatchlistItemEntity,
      StockEntity,
      OhlcvEntity,
      FinancialReportEntity,
      IndicatorEntity,
      ValuationMetricEntity,
    ]),
  ],
  controllers: [WatchlistsController],
  providers: [WatchlistsService],
})
export class WatchlistsModule {}
