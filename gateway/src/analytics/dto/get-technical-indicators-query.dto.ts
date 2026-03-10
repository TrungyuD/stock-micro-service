/**
 * get-technical-indicators-query.dto.ts — Query params for technical indicators endpoint.
 */
import { IsOptional, IsIn } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class GetTechnicalIndicatorsQueryDto {
  @ApiPropertyOptional({ description: 'Timeframe: "1d" or "1wk"', default: '1d' })
  @IsOptional()
  @IsIn(['1d', '1wk'], { message: 'timeframe must be one of: 1d, 1wk' })
  timeframe?: string = '1d';
}
