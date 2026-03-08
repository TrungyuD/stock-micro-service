/**
 * batch-analysis.dto.ts — Request body for batch analysis endpoint.
 */
import { IsArray, IsString, ArrayMaxSize, ArrayMinSize } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class BatchAnalysisDto {
  @ApiProperty({
    description: 'List of stock symbols (max 50)',
    example: ['AAPL', 'MSFT', 'GOOGL'],
  })
  @IsArray()
  @IsString({ each: true })
  @ArrayMinSize(1)
  @ArrayMaxSize(50)
  symbols: string[];
}
