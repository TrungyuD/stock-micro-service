/**
 * list-stocks-query.dto.ts — Query params for listing stocks with pagination and filters.
 */
import { IsOptional, IsString } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';
import { PaginationQueryDto } from '../../common/dto/pagination.dto';

export class ListStocksQueryDto extends PaginationQueryDto {
  @ApiPropertyOptional({ description: 'Filter by exchange (e.g., "NASDAQ")' })
  @IsOptional()
  @IsString()
  exchange?: string;

  @ApiPropertyOptional({ description: 'Filter by sector (e.g., "Technology")' })
  @IsOptional()
  @IsString()
  sector?: string;

  @ApiPropertyOptional({ description: 'Search by symbol or name' })
  @IsOptional()
  @IsString()
  search?: string;
}
