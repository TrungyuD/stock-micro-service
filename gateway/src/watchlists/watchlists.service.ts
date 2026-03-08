/**
 * watchlists.service.ts — CRUD operations for watchlists using TypeORM repositories.
 * Watchlists are gateway-local data (no gRPC — stored directly in PostgreSQL).
 */
import { Injectable, NotFoundException, ConflictException, ForbiddenException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { WatchlistEntity } from '../entities/watchlist.entity';
import { WatchlistItemEntity } from '../entities/watchlist-item.entity';

@Injectable()
export class WatchlistsService {
  constructor(
    @InjectRepository(WatchlistEntity)
    private readonly watchlistRepo: Repository<WatchlistEntity>,
    @InjectRepository(WatchlistItemEntity)
    private readonly itemRepo: Repository<WatchlistItemEntity>,
  ) {}

  /** Create a new watchlist for a user */
  async create(userId: string, name: string): Promise<WatchlistEntity> {
    try {
      const watchlist = this.watchlistRepo.create({ userId, name });
      return await this.watchlistRepo.save(watchlist);
    } catch (err: any) {
      if (err.code === '23505') {
        throw new ConflictException(`Watchlist "${name}" already exists`);
      }
      throw err;
    }
  }

  /** List all watchlists for a user */
  async findAll(userId: string): Promise<WatchlistEntity[]> {
    return this.watchlistRepo.find({
      where: { userId },
      relations: ['items', 'items.stock'],
      order: { createdAt: 'DESC' },
    });
  }

  /** Get a single watchlist by ID — verifies ownership */
  async findOne(id: number, userId: string): Promise<WatchlistEntity> {
    const watchlist = await this.watchlistRepo.findOne({
      where: { id },
      relations: ['items', 'items.stock'],
    });
    if (!watchlist) {
      throw new NotFoundException(`Watchlist #${id} not found`);
    }
    if (watchlist.userId !== userId) {
      throw new ForbiddenException('Not authorized to access this watchlist');
    }
    return watchlist;
  }

  /** Delete a watchlist (cascade deletes items) — verifies ownership */
  async remove(id: number, userId: string): Promise<void> {
    const watchlist = await this.findOne(id, userId);
    await this.watchlistRepo.delete(watchlist.id);
  }

  /** Add a stock to a watchlist — verifies ownership */
  async addItem(watchlistId: number, stockId: number, userId: string): Promise<WatchlistItemEntity> {
    await this.findOne(watchlistId, userId);

    try {
      const item = this.itemRepo.create({ watchlistId, stockId });
      return await this.itemRepo.save(item);
    } catch (err: any) {
      if (err.code === '23505') {
        throw new ConflictException('Stock already in watchlist');
      }
      if (err.code === '23503') {
        throw new NotFoundException('Stock not found');
      }
      throw err;
    }
  }

  /** Remove a stock from a watchlist — verifies ownership */
  async removeItem(watchlistId: number, stockId: number, userId: string): Promise<void> {
    await this.findOne(watchlistId, userId);

    const result = await this.itemRepo.delete({ watchlistId, stockId });
    if (result.affected === 0) {
      throw new NotFoundException('Item not found in watchlist');
    }
  }
}
