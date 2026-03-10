/**
 * get-price-history-query.dto.ts — Query params for OHLCV price history endpoint.
 */
import { IsOptional, IsString, IsInt, Min, Max, IsIn, Matches } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class GetPriceHistoryQueryDto {
  @ApiPropertyOptional({ description: 'Candle interval: "1d", "1wk", "1mo"', default: '1d' })
  @IsOptional()
  @IsIn(['1d', '1wk', '1mo'], { message: 'interval must be one of: 1d, 1wk, 1mo' })
  interval?: string = '1d';

  @ApiPropertyOptional({ description: 'Start date (YYYY-MM-DD)', example: '2025-01-01' })
  @IsOptional()
  @Matches(/^\d{4}-\d{2}-\d{2}$/, { message: 'startDate must be YYYY-MM-DD format' })
  startDate?: string;

  @ApiPropertyOptional({ description: 'End date (YYYY-MM-DD)', example: '2026-03-04' })
  @IsOptional()
  @Matches(/^\d{4}-\d{2}-\d{2}$/, { message: 'endDate must be YYYY-MM-DD format' })
  endDate?: string;

  @ApiPropertyOptional({ description: 'Max number of records', default: 365, maximum: 1000 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(1000)
  limit?: number = 365;
}
