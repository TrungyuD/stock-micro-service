import { Module } from '@nestjs/common';
import { StocksController } from './stocks.controller';
import { StocksService } from './stocks.service';

/**
 * StocksModule — handles REST endpoints for stock price and market data.
 * Delegates to Python Informer gRPC service via GrpcClientModule (global).
 */
@Module({
  controllers: [StocksController],
  providers: [StocksService],
})
export class StocksModule {}
