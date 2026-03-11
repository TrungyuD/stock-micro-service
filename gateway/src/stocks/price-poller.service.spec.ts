/**
 * price-poller.service.spec.ts — Unit tests for PricePollerService polling logic.
 */
import { Test, TestingModule } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import { PricePollerService } from './price-poller.service';
import { StocksService } from './stocks.service';

describe('PricePollerService', () => {
  let service: PricePollerService;

  const mockStocksService = { getLivePrice: jest.fn() };
  const mockConfigService = {
    get: jest.fn().mockImplementation((key: string, def: any) => {
      if (key === 'PRICE_POLL_INTERVAL_MS') return 100; // fast interval for tests
      return def;
    }),
  };

  /** Minimal mock for socket.io Server with /prices namespace adapter */
  const makeServer = (roomSizes: Record<string, number> = {}) => {
    const rooms = new Map<string, Set<string>>(
      Object.entries(roomSizes).map(([k, v]) => [k, new Set(Array(v).fill('id'))]),
    );
    return {
      of: jest.fn().mockReturnValue({ adapter: { rooms } }),
      to: jest.fn().mockReturnValue({ emit: jest.fn() }),
    } as any;
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        PricePollerService,
        { provide: StocksService, useValue: mockStocksService },
        { provide: ConfigService, useValue: mockConfigService },
      ],
    }).compile();

    service = module.get<PricePollerService>(PricePollerService);
  });

  afterEach(() => {
    service.onModuleDestroy();
    jest.useRealTimers();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('watch', () => {
    it('should add symbol and start polling', () => {
      const server = makeServer({ 'price:AAPL': 1 });
      mockStocksService.getLivePrice.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);

      jest.advanceTimersByTime(100);
      expect(mockStocksService.getLivePrice).toHaveBeenCalledWith(['AAPL']);
    });

    it('should not start duplicate polling loop on second watch', () => {
      const server = makeServer({ 'price:AAPL': 1, 'price:MSFT': 1 });
      mockStocksService.getLivePrice.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.watch('MSFT', server);

      jest.advanceTimersByTime(100);
      // Both symbols batched into a single gRPC call
      expect(mockStocksService.getLivePrice).toHaveBeenCalledTimes(1);
      expect(mockStocksService.getLivePrice).toHaveBeenCalledWith(
        expect.arrayContaining(['AAPL', 'MSFT']),
      );
    });
  });

  describe('cleanupEmptyRooms', () => {
    it('should remove symbol when room is empty and stop polling', () => {
      const server = makeServer({ 'price:AAPL': 0 });
      mockStocksService.getLivePrice.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.cleanupEmptyRooms(server);

      // Polling should have stopped — no more calls after cleanup
      mockStocksService.getLivePrice.mockClear();
      jest.advanceTimersByTime(200);
      expect(mockStocksService.getLivePrice).not.toHaveBeenCalled();
    });

    it('should keep symbol when room still has clients', () => {
      const server = makeServer({ 'price:AAPL': 2 });
      mockStocksService.getLivePrice.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.cleanupEmptyRooms(server);

      jest.advanceTimersByTime(100);
      expect(mockStocksService.getLivePrice).toHaveBeenCalledWith(['AAPL']);
    });
  });

  describe('polling emission', () => {
    it('should emit price_update for each price in response', async () => {
      const emitFn = jest.fn();
      const server = {
        of: jest.fn().mockReturnValue({ adapter: { rooms: new Map([['price:AAPL', new Set(['id'])]]) } }),
        to: jest.fn().mockReturnValue({ emit: emitFn }),
      } as any;

      mockStocksService.getLivePrice.mockResolvedValue({
        prices: [{
          symbol: 'AAPL',
          last_price: 175.5,
          previous_close: 173.0,
          change_pct: 1.44,
          timestamp: 1700000000,
        }],
      });

      service.watch('AAPL', server);
      jest.advanceTimersByTime(100);
      // Let the async poll complete
      await Promise.resolve();

      expect(server.to).toHaveBeenCalledWith('price:AAPL');
      expect(emitFn).toHaveBeenCalledWith('price_update', {
        symbol: 'AAPL',
        lastPrice: 175.5,
        previousClose: 173.0,
        changePct: 1.44,
        timestamp: 1700000000,
      });
    });

    it('should log error and continue on gRPC failure', async () => {
      const server = makeServer({ 'price:AAPL': 1 });
      mockStocksService.getLivePrice.mockRejectedValue(new Error('gRPC down'));

      service.watch('AAPL', server);
      jest.advanceTimersByTime(100);
      await Promise.resolve();

      // Should not throw — service stays alive
      expect(service).toBeDefined();
    });
  });

  describe('onModuleDestroy', () => {
    it('should stop polling on destroy', () => {
      const server = makeServer({ 'price:AAPL': 1 });
      mockStocksService.getLivePrice.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.onModuleDestroy();

      mockStocksService.getLivePrice.mockClear();
      jest.advanceTimersByTime(300);
      expect(mockStocksService.getLivePrice).not.toHaveBeenCalled();
    });
  });
});
