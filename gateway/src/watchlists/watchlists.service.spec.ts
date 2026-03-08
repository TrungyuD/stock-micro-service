import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException, ConflictException, ForbiddenException } from '@nestjs/common';
import { getRepositoryToken } from '@nestjs/typeorm';
import { WatchlistsService } from './watchlists.service';
import { WatchlistEntity } from '../entities/watchlist.entity';
import { WatchlistItemEntity } from '../entities/watchlist-item.entity';

describe('WatchlistsService', () => {
  let service: WatchlistsService;

  const mockWatchlistRepo = {
    create: jest.fn(),
    save: jest.fn(),
    find: jest.fn(),
    findOne: jest.fn(),
    delete: jest.fn(),
  };

  const mockItemRepo = {
    create: jest.fn(),
    save: jest.fn(),
    delete: jest.fn(),
  };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        WatchlistsService,
        { provide: getRepositoryToken(WatchlistEntity), useValue: mockWatchlistRepo },
        { provide: getRepositoryToken(WatchlistItemEntity), useValue: mockItemRepo },
      ],
    }).compile();

    service = module.get<WatchlistsService>(WatchlistsService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('create', () => {
    it('should create and save a watchlist', async () => {
      const watchlist = { id: 1, userId: 'user1', name: 'Tech' };
      mockWatchlistRepo.create.mockReturnValue(watchlist);
      mockWatchlistRepo.save.mockResolvedValue(watchlist);

      const result = await service.create('user1', 'Tech');
      expect(result).toEqual(watchlist);
      expect(mockWatchlistRepo.create).toHaveBeenCalledWith({ userId: 'user1', name: 'Tech' });
    });

    it('should throw ConflictException on duplicate', async () => {
      mockWatchlistRepo.create.mockReturnValue({});
      mockWatchlistRepo.save.mockRejectedValue({ code: '23505' });

      await expect(service.create('user1', 'Tech')).rejects.toThrow(ConflictException);
    });
  });

  describe('findAll', () => {
    it('should return watchlists for a user', async () => {
      const watchlists = [{ id: 1, userId: 'user1', name: 'Tech' }];
      mockWatchlistRepo.find.mockResolvedValue(watchlists);

      const result = await service.findAll('user1');
      expect(result).toEqual(watchlists);
    });
  });

  describe('findOne', () => {
    it('should return a watchlist when found and owned', async () => {
      const watchlist = { id: 1, userId: 'user1', name: 'Tech' };
      mockWatchlistRepo.findOne.mockResolvedValue(watchlist);

      const result = await service.findOne(1, 'user1');
      expect(result).toEqual(watchlist);
    });

    it('should throw NotFoundException when not found', async () => {
      mockWatchlistRepo.findOne.mockResolvedValue(null);

      await expect(service.findOne(999, 'user1')).rejects.toThrow(NotFoundException);
    });

    it('should throw ForbiddenException when not owned', async () => {
      mockWatchlistRepo.findOne.mockResolvedValue({ id: 1, userId: 'otherUser' });

      await expect(service.findOne(1, 'user1')).rejects.toThrow(ForbiddenException);
    });
  });

  describe('remove', () => {
    it('should delete a watchlist owned by user', async () => {
      const watchlist = { id: 1, userId: 'user1' };
      mockWatchlistRepo.findOne.mockResolvedValue(watchlist);
      mockWatchlistRepo.delete.mockResolvedValue({ affected: 1 });

      await service.remove(1, 'user1');
      expect(mockWatchlistRepo.delete).toHaveBeenCalledWith(1);
    });
  });

  describe('addItem', () => {
    it('should add a stock to a watchlist', async () => {
      const watchlist = { id: 1, userId: 'user1' };
      const item = { watchlistId: 1, stockId: 42 };
      mockWatchlistRepo.findOne.mockResolvedValue(watchlist);
      mockItemRepo.create.mockReturnValue(item);
      mockItemRepo.save.mockResolvedValue(item);

      const result = await service.addItem(1, 42, 'user1');
      expect(result).toEqual(item);
    });

    it('should throw ConflictException on duplicate item', async () => {
      mockWatchlistRepo.findOne.mockResolvedValue({ id: 1, userId: 'user1' });
      mockItemRepo.create.mockReturnValue({});
      mockItemRepo.save.mockRejectedValue({ code: '23505' });

      await expect(service.addItem(1, 42, 'user1')).rejects.toThrow(ConflictException);
    });
  });

  describe('removeItem', () => {
    it('should remove a stock from a watchlist', async () => {
      mockWatchlistRepo.findOne.mockResolvedValue({ id: 1, userId: 'user1' });
      mockItemRepo.delete.mockResolvedValue({ affected: 1 });

      await service.removeItem(1, 42, 'user1');
      expect(mockItemRepo.delete).toHaveBeenCalledWith({ watchlistId: 1, stockId: 42 });
    });

    it('should throw NotFoundException when item not found', async () => {
      mockWatchlistRepo.findOne.mockResolvedValue({ id: 1, userId: 'user1' });
      mockItemRepo.delete.mockResolvedValue({ affected: 0 });

      await expect(service.removeItem(1, 99, 'user1')).rejects.toThrow(NotFoundException);
    });
  });
});
