import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { StocksController } from './stocks.controller';
import { StocksService } from './stocks.service';
import { StockPriceGateway } from './stock-price.gateway';
import { PricePollerService } from './price-poller.service';

/**
 * StocksModule — REST endpoints for stock data + WebSocket gateway for live prices.
 * JwtModule imported here to provide JwtService for StockPriceGateway handshake auth.
 * GrpcClientModule (global) provides INFORMER_SERVICE to StocksService.
 */
@Module({
  imports: [JwtModule],
  controllers: [StocksController],
  providers: [StocksService, StockPriceGateway, PricePollerService],
})
export class StocksModule {}
