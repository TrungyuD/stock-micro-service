/**
 * price-poller.service.ts — Polls Informer gRPC for live prices at configurable intervals.
 * Manages a set of watched symbols and emits price_update events via socket.io rooms.
 * Prefers gRPC server-side streaming when available; falls back to interval polling.
 */
import { Injectable, Logger, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Subscription } from 'rxjs';
import { Server } from 'socket.io';
import { StocksService } from './stocks.service';

@Injectable()
export class PricePollerService implements OnModuleDestroy {
  private readonly logger = new Logger(PricePollerService.name);
  private readonly watchedSymbols = new Set<string>();
  private intervalRef: NodeJS.Timeout | null = null;
  private streamSubscription: Subscription | null = null;
  private readonly pollIntervalMs: number;

  constructor(
    private readonly stocksService: StocksService,
    private readonly configService: ConfigService,
  ) {
    this.pollIntervalMs = this.configService.get<number>('PRICE_POLL_INTERVAL_MS', 15000);
  }

  /**
   * Add a symbol to the watch set.
   * On first symbol: attempt gRPC streaming, falling back to polling if unavailable.
   * On subsequent symbols: streaming/polling loop already running — symbol is picked up automatically.
   */
  watch(symbol: string, server: Server) {
    this.watchedSymbols.add(symbol);
    if (!this.intervalRef && !this.streamSubscription) {
      this.startStreaming(server);
    }
  }

  /**
   * Remove symbols whose rooms have zero connected clients.
   * Stop polling/streaming entirely if no symbols remain.
   * Called on every client disconnect.
   */
  cleanupEmptyRooms(server: Server) {
    // Cast adapter to access rooms map on the default in-memory adapter
    const adapter = server.of('/prices').adapter as unknown as { rooms: Map<string, Set<string>> };
    for (const symbol of this.watchedSymbols) {
      const room = adapter.rooms?.get(`price:${symbol}`);
      if (!room || room.size === 0) {
        this.watchedSymbols.delete(symbol);
        this.logger.debug(`Removed unwatched symbol: ${symbol}`);
      }
    }
    if (this.watchedSymbols.size === 0) {
      this.stopAll();
    }
  }

  /**
   * Attempt to start gRPC server-side streaming for watched symbols.
   * Falls back to polling if the stream errors immediately or is unavailable.
   */
  private startStreaming(server: Server) {
    try {
      const symbols = [...this.watchedSymbols];
      const stream$ = this.stocksService.streamPrices(symbols, this.pollIntervalMs);
      this.streamSubscription = stream$.subscribe({
        next: (update: any) => {
          server.to(`price:${update.symbol}`).emit('price_update', {
            symbol: update.symbol,
            lastPrice: update.last_price,
            previousClose: update.previous_close,
            changePct: update.change_pct,
            timestamp: Number(update.timestamp),
          });
        },
        error: (err: Error) => {
          this.logger.warn(`Stream disconnected, falling back to polling: ${err.message}`);
          this.streamSubscription = null;
          this.startPolling(server);
        },
        complete: () => {
          this.logger.debug('StreamPrices completed — restarting polling');
          this.streamSubscription = null;
          if (this.watchedSymbols.size > 0) {
            this.startPolling(server);
          }
        },
      });
      this.logger.log(`Started gRPC streaming for ${symbols.length} symbol(s)`);
    } catch (err) {
      this.logger.warn(`StreamPrices unavailable, using polling: ${(err as Error).message}`);
      this.startPolling(server);
    }
  }

  /** Start the interval loop that batches all watched symbols into one gRPC call */
  private startPolling(server: Server) {
    this.logger.log(`Starting price polling every ${this.pollIntervalMs}ms`);
    this.intervalRef = setInterval(async () => {
      if (this.watchedSymbols.size === 0) {
        this.stopAll();
        return;
      }
      try {
        const symbols = [...this.watchedSymbols];
        const response = await this.stocksService.getLatestPrices(symbols);
        const prices: any[] = response?.prices ?? [];
        for (const price of prices) {
          server.to(`price:${price.symbol}`).emit('price_update', {
            symbol: price.symbol,
            lastPrice: price.last_price,
            previousClose: price.previous_close,
            changePct: price.change_pct,
            timestamp: Number(price.timestamp),
          });
        }
      } catch (err) {
        this.logger.error(`Price poll failed: ${(err as Error).message}`);
      }
    }, this.pollIntervalMs);
  }

  private stopAll() {
    if (this.intervalRef) {
      clearInterval(this.intervalRef);
      this.intervalRef = null;
      this.logger.log('Stopped price polling (no active watchers)');
    }
    if (this.streamSubscription) {
      this.streamSubscription.unsubscribe();
      this.streamSubscription = null;
      this.logger.log('Stopped gRPC stream (no active watchers)');
    }
  }

  onModuleDestroy() {
    this.stopAll();
  }
}
