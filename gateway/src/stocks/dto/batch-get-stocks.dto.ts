/**
 * batch-get-stocks.dto.ts — Request body for batch-getting multiple stocks.
 */
import { IsArray, IsString, ArrayMaxSize, ArrayMinSize, Matches } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class BatchGetStocksDto {
  @ApiProperty({
    description: 'List of stock symbols (max 50)',
    example: ['AAPL', 'MSFT', 'GOOGL'],
  })
  @IsArray()
  @IsString({ each: true })
  @Matches(/^[A-Za-z0-9.]{1,10}$/, { each: true, message: 'each symbol must be 1-10 alphanumeric chars or dots' })
  @ArrayMinSize(1)
  @ArrayMaxSize(50)
  symbols: string[];
}
