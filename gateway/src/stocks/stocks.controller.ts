import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { StocksService } from './stocks.service';

/**
 * StocksController — REST endpoints for stock data.
 * Full implementation in Phase 6.
 */
@ApiTags('stocks')
@Controller('stocks')
export class StocksController {
  constructor(private readonly stocksService: StocksService) {}

  @Get()
  @ApiOperation({ summary: 'List tracked stocks (placeholder)' })
  findAll() {
    return this.stocksService.findAll();
  }

  @Get(':symbol')
  @ApiOperation({ summary: 'Get stock by symbol (placeholder)' })
  findOne(@Param('symbol') symbol: string) {
    return this.stocksService.findOne(symbol);
  }
}
