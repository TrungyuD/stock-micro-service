/**
 * stocks.controller.ts — REST endpoints for stock data.
 * Proxies to Informer gRPC service via StocksService.
 */
import { Controller, Get, Post, Param, Query, Body } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiParam, ApiResponse } from '@nestjs/swagger';
import { StocksService } from './stocks.service';
import { ListStocksQueryDto } from './dto/list-stocks-query.dto';
import { GetPriceHistoryQueryDto } from './dto/get-price-history-query.dto';
import { GetFinancialReportsQueryDto } from './dto/get-financial-reports-query.dto';
import { BatchGetStocksDto } from './dto/batch-get-stocks.dto';

@ApiTags('stocks')
@Controller('stocks')
export class StocksController {
  constructor(private readonly stocksService: StocksService) {}

  @Get()
  @ApiOperation({ summary: 'List tracked stocks with pagination and filters' })
  @ApiResponse({ status: 200, description: 'Paginated stock list' })
  findAll(@Query() query: ListStocksQueryDto) {
    return this.stocksService.listStocks(query);
  }

  @Post('batch')
  @ApiOperation({ summary: 'Batch-get multiple stocks by symbols (max 50)' })
  @ApiResponse({ status: 200, description: 'Batch stock results' })
  batchGetStocks(@Body() dto: BatchGetStocksDto) {
    return this.stocksService.batchGetStocks(dto.symbols);
  }

  @Get(':symbol')
  @ApiOperation({ summary: 'Get stock metadata by symbol' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'Stock info' })
  @ApiResponse({ status: 404, description: 'Stock not found' })
  findOne(@Param('symbol') symbol: string) {
    return this.stocksService.getStockInfo(symbol.toUpperCase());
  }

  @Get(':symbol/prices')
  @ApiOperation({ summary: 'Get OHLCV price history for a symbol' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'OHLCV candle data' })
  getPriceHistory(
    @Param('symbol') symbol: string,
    @Query() query: GetPriceHistoryQueryDto,
  ) {
    return this.stocksService.getPriceHistory(symbol.toUpperCase(), query);
  }

  @Get(':symbol/financials')
  @ApiOperation({ summary: 'Get financial reports for a symbol' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'Financial reports list' })
  getFinancialReports(
    @Param('symbol') symbol: string,
    @Query() query: GetFinancialReportsQueryDto,
  ) {
    return this.stocksService.getFinancialReports(symbol.toUpperCase(), query);
  }
}
