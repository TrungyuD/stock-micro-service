/**
 * watchlists.controller.ts — REST endpoints for watchlist CRUD operations.
 * All endpoints require JWT authentication. UserId extracted from token.
 */
import {
  Controller,
  Get,
  Post,
  Delete,
  Param,
  Body,
  ParseIntPipe,
  UseGuards,
  HttpCode,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { WatchlistsService } from './watchlists.service';
import { CreateWatchlistDto } from './dto/create-watchlist.dto';
import { AddWatchlistItemDto } from './dto/add-watchlist-item.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../auth/decorators/current-user.decorator';

@ApiTags('watchlists')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('watchlists')
export class WatchlistsController {
  constructor(private readonly watchlistsService: WatchlistsService) {}

  @Get()
  @ApiOperation({ summary: 'List all watchlists for current user' })
  @ApiResponse({ status: 200, description: 'List of watchlists' })
  findAll(@CurrentUser('userId') userId: string) {
    return this.watchlistsService.findAll(userId);
  }

  @Post()
  @ApiOperation({ summary: 'Create a new watchlist' })
  @ApiResponse({ status: 201, description: 'Created watchlist' })
  @ApiResponse({ status: 409, description: 'Watchlist name already exists' })
  create(
    @Body() dto: CreateWatchlistDto,
    @CurrentUser('userId') userId: string,
  ) {
    return this.watchlistsService.create(userId, dto.name);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get watchlist by ID with stock items' })
  @ApiResponse({ status: 200, description: 'Watchlist with items' })
  @ApiResponse({ status: 404, description: 'Watchlist not found' })
  @ApiResponse({ status: 403, description: 'Not authorized' })
  findOne(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser('userId') userId: string,
  ) {
    return this.watchlistsService.findOne(id, userId);
  }

  @Delete(':id')
  @HttpCode(204)
  @ApiOperation({ summary: 'Delete a watchlist' })
  @ApiResponse({ status: 204, description: 'Watchlist deleted' })
  @ApiResponse({ status: 404, description: 'Watchlist not found' })
  @ApiResponse({ status: 403, description: 'Not authorized' })
  remove(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser('userId') userId: string,
  ) {
    return this.watchlistsService.remove(id, userId);
  }

  @Post(':id/items')
  @ApiOperation({ summary: 'Add a stock to a watchlist' })
  @ApiResponse({ status: 201, description: 'Stock added to watchlist' })
  @ApiResponse({ status: 404, description: 'Watchlist or stock not found' })
  @ApiResponse({ status: 409, description: 'Stock already in watchlist' })
  addItem(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: AddWatchlistItemDto,
    @CurrentUser('userId') userId: string,
  ) {
    return this.watchlistsService.addItem(id, dto.stockId, userId);
  }

  @Delete(':id/items/:stockId')
  @HttpCode(204)
  @ApiOperation({ summary: 'Remove a stock from a watchlist' })
  @ApiResponse({ status: 204, description: 'Stock removed from watchlist' })
  @ApiResponse({ status: 404, description: 'Item not found' })
  @ApiResponse({ status: 403, description: 'Not authorized' })
  removeItem(
    @Param('id', ParseIntPipe) id: number,
    @Param('stockId', ParseIntPipe) stockId: number,
    @CurrentUser('userId') userId: string,
  ) {
    return this.watchlistsService.removeItem(id, stockId, userId);
  }
}
