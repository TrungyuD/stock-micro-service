/**
 * stock-price.gateway.ts — WebSocket gateway for live stock price updates.
 * Authenticates via JWT on handshake, manages per-symbol rooms.
 * Namespace: /prices
 */
import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  ConnectedSocket,
  MessageBody,
} from '@nestjs/websockets';
import { Logger } from '@nestjs/common';
import { Server, Socket } from 'socket.io';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { PricePollerService } from './price-poller.service';

@WebSocketGateway({
  namespace: '/prices',
  cors: { origin: true, credentials: true },
})
export class StockPriceGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer() server: Server;
  private readonly logger = new Logger(StockPriceGateway.name);

  constructor(
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
    private readonly pollerService: PricePollerService,
  ) {}

  /** Verify JWT on WebSocket handshake; disconnect if invalid */
  async handleConnection(client: Socket) {
    try {
      const token = client.handshake.auth?.token;
      if (!token) throw new Error('No token provided');
      this.jwtService.verify(token, {
        secret: this.configService.get<string>('JWT_SECRET'),
      });
      this.logger.log(`Client connected: ${client.id}`);
    } catch (err) {
      this.logger.warn(`Unauthorized WS connection: ${client.id} — ${(err as Error).message}`);
      client.disconnect();
    }
  }

  /** Clean up empty rooms when a client disconnects */
  handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);
    this.pollerService.cleanupEmptyRooms(this.server);
  }

  /** Subscribe client to a symbol's price room */
  @SubscribeMessage('subscribe')
  handleSubscribe(
    @ConnectedSocket() client: Socket,
    @MessageBody() symbol: string,
  ) {
    const normalized = symbol?.toUpperCase().trim();
    if (!normalized) return;
    client.join(`price:${normalized}`);
    this.pollerService.watch(normalized, this.server);
    this.logger.debug(`${client.id} subscribed to ${normalized}`);
  }

  /** Unsubscribe client from a symbol's price room */
  @SubscribeMessage('unsubscribe')
  handleUnsubscribe(
    @ConnectedSocket() client: Socket,
    @MessageBody() symbol: string,
  ) {
    const normalized = symbol?.toUpperCase().trim();
    if (!normalized) return;
    client.leave(`price:${normalized}`);
    this.logger.debug(`${client.id} unsubscribed from ${normalized}`);
  }
}
