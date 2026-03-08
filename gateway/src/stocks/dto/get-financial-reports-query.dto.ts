/**
 * get-financial-reports-query.dto.ts — Query params for financial reports endpoint.
 */
import { IsOptional, IsString, IsInt, Min, Max } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class GetFinancialReportsQueryDto {
  @ApiPropertyOptional({ description: 'Report type: "Annual" or "Quarterly"' })
  @IsOptional()
  @IsString()
  reportType?: string;

  @ApiPropertyOptional({ description: 'Number of years of history', default: 5, maximum: 20 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(20)
  yearsBack?: number = 5;
}
