import { Injectable } from '@nestjs/common';

/**
 * StocksService — placeholder service for stock data.
 * Will be wired to Informer gRPC client in Phase 6.
 */
@Injectable()
export class StocksService {
  findAll() {
    return { message: 'StocksService placeholder — Phase 6 implementation pending' };
  }

  findOne(symbol: string) {
    return { symbol, message: 'StocksService placeholder — Phase 6 implementation pending' };
  }
}
