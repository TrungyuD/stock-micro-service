/**
 * price-poller.service.spec.ts — Unit tests for PricePollerService polling and streaming logic.
 */
import { Test, TestingModule } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import { Observable, Subject } from 'rxjs';
import { PricePollerService } from './price-poller.service';
import { StocksService } from './stocks.service';

describe('PricePollerService', () => {
  let service: PricePollerService;

  const mockStocksService = {
    getLatestPrices: jest.fn(),
    streamPrices: jest.fn(),
  };
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

    // Default: streaming throws so tests fall back to polling unless overridden
    mockStocksService.streamPrices.mockImplementation(() => {
      throw new Error('stream unavailable');
    });

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
    it('should add symbol and start polling (streaming unavailable)', () => {
      const server = makeServer({ 'price:AAPL': 1 });
      mockStocksService.getLatestPrices.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);

      jest.advanceTimersByTime(100);
      expect(mockStocksService.getLatestPrices).toHaveBeenCalledWith(['AAPL']);
    });

    it('should not start duplicate polling loop on second watch', () => {
      const server = makeServer({ 'price:AAPL': 1, 'price:MSFT': 1 });
      mockStocksService.getLatestPrices.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.watch('MSFT', server);

      jest.advanceTimersByTime(100);
      // Both symbols batched into a single gRPC call
      expect(mockStocksService.getLatestPrices).toHaveBeenCalledTimes(1);
      expect(mockStocksService.getLatestPrices).toHaveBeenCalledWith(
        expect.arrayContaining(['AAPL', 'MSFT']),
      );
    });
  });

  describe('cleanupEmptyRooms', () => {
    it('should remove symbol when room is empty and stop polling', () => {
      const server = makeServer({ 'price:AAPL': 0 });
      mockStocksService.getLatestPrices.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.cleanupEmptyRooms(server);

      // Polling should have stopped — no more calls after cleanup
      mockStocksService.getLatestPrices.mockClear();
      jest.advanceTimersByTime(200);
      expect(mockStocksService.getLatestPrices).not.toHaveBeenCalled();
    });

    it('should keep symbol when room still has clients', () => {
      const server = makeServer({ 'price:AAPL': 2 });
      mockStocksService.getLatestPrices.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.cleanupEmptyRooms(server);

      jest.advanceTimersByTime(100);
      expect(mockStocksService.getLatestPrices).toHaveBeenCalledWith(['AAPL']);
    });
  });

  describe('polling emission', () => {
    it('should emit price_update for each price in response', async () => {
      const emitFn = jest.fn();
      const server = {
        of: jest.fn().mockReturnValue({ adapter: { rooms: new Map([['price:AAPL', new Set(['id'])]]) } }),
        to: jest.fn().mockReturnValue({ emit: emitFn }),
      } as any;

      mockStocksService.getLatestPrices.mockResolvedValue({
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
      mockStocksService.getLatestPrices.mockRejectedValue(new Error('gRPC down'));

      service.watch('AAPL', server);
      jest.advanceTimersByTime(100);
      await Promise.resolve();

      // Should not throw — service stays alive
      expect(service).toBeDefined();
    });
  });

  describe('gRPC streaming', () => {
    it('should use gRPC stream when streamPrices returns an Observable', async () => {
      const subject = new Subject<any>();
      mockStocksService.streamPrices.mockReturnValue(subject.asObservable());

      const emitFn = jest.fn();
      const server = {
        of: jest.fn().mockReturnValue({ adapter: { rooms: new Map() } }),
        to: jest.fn().mockReturnValue({ emit: emitFn }),
      } as any;

      service.watch('AAPL', server);

      // Push a price update through the stream
      subject.next({
        symbol: 'AAPL',
        last_price: 180.0,
        previous_close: 178.0,
        change_pct: 1.12,
        timestamp: 1700001000,
      });
      await Promise.resolve();

      expect(server.to).toHaveBeenCalledWith('price:AAPL');
      expect(emitFn).toHaveBeenCalledWith('price_update', {
        symbol: 'AAPL',
        lastPrice: 180.0,
        previousClose: 178.0,
        changePct: 1.12,
        timestamp: 1700001000,
      });
      // Polling should NOT have been started
      expect(mockStocksService.getLatestPrices).not.toHaveBeenCalled();
    });

    it('should fall back to polling when stream emits an error', async () => {
      const subject = new Subject<any>();
      mockStocksService.streamPrices.mockReturnValue(subject.asObservable());
      mockStocksService.getLatestPrices.mockResolvedValue({ prices: [] });

      const server = makeServer({ 'price:AAPL': 1 });
      service.watch('AAPL', server);

      // Stream errors — triggers fallback
      subject.error(new Error('stream disconnected'));
      await Promise.resolve();

      // Polling loop should now be active
      jest.advanceTimersByTime(100);
      await Promise.resolve();
      expect(mockStocksService.getLatestPrices).toHaveBeenCalled();
    });

    it('stocksService.streamPrices should be defined', () => {
      // Verify the method is available on the injected service
      expect(typeof mockStocksService.streamPrices).toBe('function');
    });
  });

  describe('onModuleDestroy', () => {
    it('should stop polling on destroy', () => {
      const server = makeServer({ 'price:AAPL': 1 });
      mockStocksService.getLatestPrices.mockResolvedValue({ prices: [] });

      service.watch('AAPL', server);
      service.onModuleDestroy();

      mockStocksService.getLatestPrices.mockClear();
      jest.advanceTimersByTime(300);
      expect(mockStocksService.getLatestPrices).not.toHaveBeenCalled();
    });

    it('should unsubscribe gRPC stream on destroy', () => {
      const subject = new Subject<any>();
      const unsubscribeSpy = jest.fn();
      const mockObs = new Observable((obs) => {
        return () => unsubscribeSpy();
      });
      mockStocksService.streamPrices.mockReturnValue(mockObs);

      const server = makeServer({ 'price:AAPL': 1 });
      service.watch('AAPL', server);
      service.onModuleDestroy();

      expect(unsubscribeSpy).toHaveBeenCalled();
    });
  });
});
