/**
 * get-technical-indicators-query.dto.ts — Query params for technical indicators endpoint.
 */
import { IsOptional, IsString } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class GetTechnicalIndicatorsQueryDto {
  @ApiPropertyOptional({ description: 'Timeframe: "1d" or "1wk"', default: '1d' })
  @IsOptional()
  @IsString()
  timeframe?: string = '1d';
}
