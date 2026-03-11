/**
 * stock-price.gateway.spec.ts — Unit tests for StockPriceGateway WebSocket handling.
 */
import { Test, TestingModule } from '@nestjs/testing';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { StockPriceGateway } from './stock-price.gateway';
import { PricePollerService } from './price-poller.service';

describe('StockPriceGateway', () => {
  let gateway: StockPriceGateway;

  const mockJwtService = { verify: jest.fn() };
  const mockConfigService = { get: jest.fn().mockReturnValue('test-secret') };
  const mockPollerService = {
    watch: jest.fn(),
    cleanupEmptyRooms: jest.fn(),
  };

  const makeSocket = (token?: string) => ({
    id: 'socket-1',
    handshake: { auth: token ? { token } : {} },
    join: jest.fn(),
    leave: jest.fn(),
    disconnect: jest.fn(),
  });

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        StockPriceGateway,
        { provide: JwtService, useValue: mockJwtService },
        { provide: ConfigService, useValue: mockConfigService },
        { provide: PricePollerService, useValue: mockPollerService },
      ],
    }).compile();

    gateway = module.get<StockPriceGateway>(StockPriceGateway);
  });

  it('should be defined', () => {
    expect(gateway).toBeDefined();
  });

  describe('handleConnection', () => {
    it('should allow connection with valid JWT', async () => {
      mockJwtService.verify.mockReturnValue({ sub: 1 });
      const client = makeSocket('valid-token') as any;

      await gateway.handleConnection(client);

      expect(mockJwtService.verify).toHaveBeenCalledWith('valid-token', { secret: 'test-secret' });
      expect(client.disconnect).not.toHaveBeenCalled();
    });

    it('should disconnect if no token provided', async () => {
      const client = makeSocket() as any;

      await gateway.handleConnection(client);

      expect(client.disconnect).toHaveBeenCalled();
    });

    it('should disconnect if JWT verification throws', async () => {
      mockJwtService.verify.mockImplementation(() => { throw new Error('invalid'); });
      const client = makeSocket('bad-token') as any;

      await gateway.handleConnection(client);

      expect(client.disconnect).toHaveBeenCalled();
    });
  });

  describe('handleDisconnect', () => {
    it('should call pollerService.cleanupEmptyRooms', () => {
      const mockServer = {} as any;
      gateway.server = mockServer;
      const client = makeSocket('token') as any;

      gateway.handleDisconnect(client);

      expect(mockPollerService.cleanupEmptyRooms).toHaveBeenCalledWith(mockServer);
    });
  });

  describe('handleSubscribe', () => {
    it('should join room and start watching normalized symbol', () => {
      const mockServer = {} as any;
      gateway.server = mockServer;
      const client = makeSocket('token') as any;

      gateway.handleSubscribe(client, 'aapl');

      expect(client.join).toHaveBeenCalledWith('price:AAPL');
      expect(mockPollerService.watch).toHaveBeenCalledWith('AAPL', mockServer);
    });

    it('should ignore empty symbol', () => {
      const client = makeSocket('token') as any;

      gateway.handleSubscribe(client, '');

      expect(client.join).not.toHaveBeenCalled();
    });
  });

  describe('handleUnsubscribe', () => {
    it('should leave room for normalized symbol', () => {
      const client = makeSocket('token') as any;

      gateway.handleUnsubscribe(client, 'msft');

      expect(client.leave).toHaveBeenCalledWith('price:MSFT');
    });

    it('should ignore empty symbol', () => {
      const client = makeSocket('token') as any;

      gateway.handleUnsubscribe(client, '');

      expect(client.leave).not.toHaveBeenCalled();
    });
  });
});
