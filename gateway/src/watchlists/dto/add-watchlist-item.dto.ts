/**
 * add-watchlist-item.dto.ts — Request body for adding a stock to a watchlist.
 */
import { IsInt, IsPositive } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class AddWatchlistItemDto {
  @ApiProperty({ description: 'Stock ID to add', example: 1 })
  @IsInt()
  @IsPositive()
  stockId: number;
}
