/**
 * stocks.controller.ts — REST endpoints for stock data.
 * Proxies to Informer gRPC service via StocksService.
 */
import { Controller, Get, Post, Put, Delete, Param, Query, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiParam, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { StocksService } from './stocks.service';
import { ListStocksQueryDto } from './dto/list-stocks-query.dto';
import { GetPriceHistoryQueryDto } from './dto/get-price-history-query.dto';
import { GetFinancialReportsQueryDto } from './dto/get-financial-reports-query.dto';
import { BatchGetStocksDto } from './dto/batch-get-stocks.dto';
import { CreateStockDto } from './dto/create-stock.dto';
import { UpdateStockDto } from './dto/update-stock.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { RolesGuard } from '../auth/guards/roles.guard';
import { Roles } from '../auth/decorators/roles.decorator';

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

  @Post()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create a new stock (admin only)' })
  @ApiResponse({ status: 201, description: 'Stock created' })
  createStock(@Body() dto: CreateStockDto) {
    return this.stocksService.createStock(dto);
  }

  @Put(':symbol')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update a stock by symbol (admin only)' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'Stock updated' })
  updateStock(@Param('symbol') symbol: string, @Body() dto: UpdateStockDto) {
    return this.stocksService.updateStock(symbol, dto);
  }

  @Delete(':symbol')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Soft-delete a stock by symbol (admin only)' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'Stock deactivated' })
  deleteStock(@Param('symbol') symbol: string) {
    return this.stocksService.deleteStock(symbol);
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
