/**
 * live-price.dto.ts — DTO for live price WebSocket events.
 * Mirrors the LivePrice message from informer.proto.
 */
export class LivePriceDto {
  symbol: string;
  lastPrice: number;
  previousClose: number;
  changePct: number;
  timestamp: number;
}
