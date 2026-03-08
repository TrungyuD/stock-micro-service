/**
 * create-watchlist.dto.ts — Request body for creating a new watchlist.
 */
import { IsString, IsNotEmpty, MaxLength } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateWatchlistDto {
  @ApiProperty({ description: 'Watchlist name', example: 'Tech Stocks' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  name: string;
}
