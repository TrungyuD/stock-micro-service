/**
 * watchlists.controller.ts — REST endpoints for watchlist CRUD operations.
 * Uses X-User-Id header for MVP (no auth yet). Replace with JWT-extracted userId later.
 */
import {
  Controller,
  Get,
  Post,
  Delete,
  Param,
  Body,
  ParseIntPipe,
  Headers,
  HttpCode,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiHeader } from '@nestjs/swagger';
import { WatchlistsService } from './watchlists.service';
import { CreateWatchlistDto } from './dto/create-watchlist.dto';
import { AddWatchlistItemDto } from './dto/add-watchlist-item.dto';

/** Default user ID for MVP (no auth). Frontend sends X-User-Id header. */
const DEFAULT_USER_ID = 'anonymous';

@ApiTags('watchlists')
@Controller('watchlists')
export class WatchlistsController {
  constructor(private readonly watchlistsService: WatchlistsService) {}

  @Get()
  @ApiOperation({ summary: 'List all watchlists for current user' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID (MVP)' })
  @ApiResponse({ status: 200, description: 'List of watchlists' })
  findAll(@Headers('x-user-id') userId?: string) {
    return this.watchlistsService.findAll(userId || DEFAULT_USER_ID);
  }

  @Post()
  @ApiOperation({ summary: 'Create a new watchlist' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID (MVP)' })
  @ApiResponse({ status: 201, description: 'Created watchlist' })
  @ApiResponse({ status: 409, description: 'Watchlist name already exists' })
  create(
    @Body() dto: CreateWatchlistDto,
    @Headers('x-user-id') userId?: string,
  ) {
    return this.watchlistsService.create(userId || DEFAULT_USER_ID, dto.name);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get watchlist by ID with stock items' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID (MVP)' })
  @ApiResponse({ status: 200, description: 'Watchlist with items' })
  @ApiResponse({ status: 404, description: 'Watchlist not found' })
  @ApiResponse({ status: 403, description: 'Not authorized' })
  findOne(
    @Param('id', ParseIntPipe) id: number,
    @Headers('x-user-id') userId?: string,
  ) {
    return this.watchlistsService.findOne(id, userId || DEFAULT_USER_ID);
  }

  @Delete(':id')
  @HttpCode(204)
  @ApiOperation({ summary: 'Delete a watchlist' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID (MVP)' })
  @ApiResponse({ status: 204, description: 'Watchlist deleted' })
  @ApiResponse({ status: 404, description: 'Watchlist not found' })
  @ApiResponse({ status: 403, description: 'Not authorized' })
  remove(
    @Param('id', ParseIntPipe) id: number,
    @Headers('x-user-id') userId?: string,
  ) {
    return this.watchlistsService.remove(id, userId || DEFAULT_USER_ID);
  }

  @Post(':id/items')
  @ApiOperation({ summary: 'Add a stock to a watchlist' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID (MVP)' })
  @ApiResponse({ status: 201, description: 'Stock added to watchlist' })
  @ApiResponse({ status: 404, description: 'Watchlist or stock not found' })
  @ApiResponse({ status: 409, description: 'Stock already in watchlist' })
  addItem(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: AddWatchlistItemDto,
    @Headers('x-user-id') userId?: string,
  ) {
    return this.watchlistsService.addItem(id, dto.stockId, userId || DEFAULT_USER_ID);
  }

  @Delete(':id/items/:stockId')
  @HttpCode(204)
  @ApiOperation({ summary: 'Remove a stock from a watchlist' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID (MVP)' })
  @ApiResponse({ status: 204, description: 'Stock removed from watchlist' })
  @ApiResponse({ status: 404, description: 'Item not found' })
  @ApiResponse({ status: 403, description: 'Not authorized' })
  removeItem(
    @Param('id', ParseIntPipe) id: number,
    @Param('stockId', ParseIntPipe) stockId: number,
    @Headers('x-user-id') userId?: string,
  ) {
    return this.watchlistsService.removeItem(id, stockId, userId || DEFAULT_USER_ID);
  }
}
