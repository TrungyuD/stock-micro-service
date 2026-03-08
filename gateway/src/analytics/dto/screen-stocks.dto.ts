/**
 * screen-stocks.dto.ts — Request body for the stock screening endpoint.
 */
import { IsOptional, IsNumber, IsBoolean, IsString, IsInt, Min, Max } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class ScreenStocksDto {
  @ApiPropertyOptional({ description: 'Minimum P/E ratio' })
  @IsOptional()
  @IsNumber()
  minPe?: number;

  @ApiPropertyOptional({ description: 'Maximum P/E ratio' })
  @IsOptional()
  @IsNumber()
  maxPe?: number;

  @ApiPropertyOptional({ description: 'Minimum PEG ratio' })
  @IsOptional()
  @IsNumber()
  minPeg?: number;

  @ApiPropertyOptional({ description: 'Maximum PEG ratio' })
  @IsOptional()
  @IsNumber()
  maxPeg?: number;

  @ApiPropertyOptional({ description: 'Minimum dividend yield' })
  @IsOptional()
  @IsNumber()
  minDividendYield?: number;

  @ApiPropertyOptional({ description: 'Maximum dividend yield' })
  @IsOptional()
  @IsNumber()
  maxDividendYield?: number;

  @ApiPropertyOptional({ description: 'Filter RSI oversold (< 30)' })
  @IsOptional()
  @IsBoolean()
  rsiOversold?: boolean;

  @ApiPropertyOptional({ description: 'Filter RSI overbought (> 70)' })
  @IsOptional()
  @IsBoolean()
  rsiOverbought?: boolean;

  @ApiPropertyOptional({ description: 'Trend direction: "Bullish" or "Bearish"' })
  @IsOptional()
  @IsString()
  trendDirection?: string;

  @ApiPropertyOptional({ description: 'Filter by sector' })
  @IsOptional()
  @IsString()
  sector?: string;

  @ApiPropertyOptional({ description: 'Max results', default: 20 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 20;

  @ApiPropertyOptional({ description: 'Sort field (e.g., "valuation_score", "pe_ratio")' })
  @IsOptional()
  @IsString()
  sortBy?: string;
}
