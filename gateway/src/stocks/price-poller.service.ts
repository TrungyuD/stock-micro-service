/**
 * price-poller.service.ts — Polls Informer gRPC for live prices at configurable intervals.
 * Manages a set of watched symbols and emits price_update events via socket.io rooms.
 */
import { Injectable, Logger, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Server } from 'socket.io';
import { StocksService } from './stocks.service';

@Injectable()
export class PricePollerService implements OnModuleDestroy {
  private readonly logger = new Logger(PricePollerService.name);
  private readonly watchedSymbols = new Set<string>();
  private intervalRef: NodeJS.Timeout | null = null;
  private readonly pollIntervalMs: number;

  constructor(
    private readonly stocksService: StocksService,
    private readonly configService: ConfigService,
  ) {
    this.pollIntervalMs = this.configService.get<number>('PRICE_POLL_INTERVAL_MS', 15000);
  }

  /**
   * Add a symbol to the watch set and start the polling loop if not running.
   * Called each time a client subscribes to a new symbol.
   */
  watch(symbol: string, server: Server) {
    this.watchedSymbols.add(symbol);
    if (!this.intervalRef) {
      this.startPolling(server);
    }
  }

  /**
   * Remove symbols whose rooms have zero connected clients.
   * Stop polling entirely if no symbols remain.
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
      this.stopPolling();
    }
  }

  /** Start the interval loop that batches all watched symbols into one gRPC call */
  private startPolling(server: Server) {
    this.logger.log(`Starting price polling every ${this.pollIntervalMs}ms`);
    this.intervalRef = setInterval(async () => {
      if (this.watchedSymbols.size === 0) {
        this.stopPolling();
        return;
      }
      try {
        const symbols = [...this.watchedSymbols];
        const response = await this.stocksService.getLivePrice(symbols);
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

  private stopPolling() {
    if (this.intervalRef) {
      clearInterval(this.intervalRef);
      this.intervalRef = null;
      this.logger.log('Stopped price polling (no active watchers)');
    }
  }

  onModuleDestroy() {
    this.stopPolling();
  }
}
