/**
 * watchlists.module.ts — NestJS module for watchlist CRUD operations.
 * Uses TypeORM repositories for direct DB access (no gRPC needed).
 * Only registers entities this module actually queries.
 */
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { WatchlistsController } from './watchlists.controller';
import { WatchlistsService } from './watchlists.service';
import { WatchlistEntity } from '../entities/watchlist.entity';
import { WatchlistItemEntity } from '../entities/watchlist-item.entity';
import { StockEntity } from '../entities/stock.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      WatchlistEntity,
      WatchlistItemEntity,
      StockEntity,           // needed for items.stock relation join
    ]),
  ],
  controllers: [WatchlistsController],
  providers: [WatchlistsService],
})
export class WatchlistsModule {}
