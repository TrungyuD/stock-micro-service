/**
 * get-stock-analysis-query.dto.ts — Query params for combined stock analysis endpoint.
 */
import { IsOptional, IsBoolean } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class GetStockAnalysisQueryDto {
  @ApiPropertyOptional({ description: 'Include AI rationale text', default: false })
  @IsOptional()
  @IsBoolean()
  includeRationale?: boolean = false;
}
