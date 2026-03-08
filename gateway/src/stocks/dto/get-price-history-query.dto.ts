/**
 * get-price-history-query.dto.ts — Query params for OHLCV price history endpoint.
 */
import { IsOptional, IsString, IsInt, Min, Max } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class GetPriceHistoryQueryDto {
  @ApiPropertyOptional({ description: 'Candle interval: "1d", "1wk", "1mo"', default: '1d' })
  @IsOptional()
  @IsString()
  interval?: string = '1d';

  @ApiPropertyOptional({ description: 'Start date in ISO 8601 (e.g., "2025-01-01")' })
  @IsOptional()
  @IsString()
  startDate?: string;

  @ApiPropertyOptional({ description: 'End date in ISO 8601 (e.g., "2026-03-04")' })
  @IsOptional()
  @IsString()
  endDate?: string;

  @ApiPropertyOptional({ description: 'Max number of records', default: 365, maximum: 1000 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(1000)
  limit?: number = 365;
}
