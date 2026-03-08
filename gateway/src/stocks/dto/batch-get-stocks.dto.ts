/**
 * batch-get-stocks.dto.ts — Request body for batch-getting multiple stocks.
 */
import { IsArray, IsString, ArrayMaxSize, ArrayMinSize } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class BatchGetStocksDto {
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
