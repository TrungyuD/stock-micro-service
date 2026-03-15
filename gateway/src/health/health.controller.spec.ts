import { Test, TestingModule } from '@nestjs/testing';
import { of, throwError } from 'rxjs';
import { DataSource } from 'typeorm';
import { HealthController } from './health.controller';

describe('HealthController', () => {
  let controller: HealthController;

  const mockInformerGrpcService = { Check: jest.fn() };
  const mockAnalyticsGrpcService = { Check: jest.fn() };

  const mockInformerClient = {
    getService: jest.fn().mockReturnValue(mockInformerGrpcService),
  };
  const mockAnalyticsClient = {
    getService: jest.fn().mockReturnValue(mockAnalyticsGrpcService),
  };
  const mockDataSource = { query: jest.fn() };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      controllers: [HealthController],
      providers: [
        { provide: 'INFORMER_SERVICE', useValue: mockInformerClient },
        { provide: 'ANALYTICS_SERVICE', useValue: mockAnalyticsClient },
        { provide: DataSource, useValue: mockDataSource },
      ],
    }).compile();

    controller = module.get<HealthController>(HealthController);
    controller.onModuleInit();
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('check — all services up', () => {
    it('should return ok when all services healthy', async () => {
      mockInformerGrpcService.Check.mockReturnValue(of({ status: 'SERVING' }));
      mockAnalyticsGrpcService.Check.mockReturnValue(of({ status: 'SERVING' }));
      mockDataSource.query.mockResolvedValue([{ '?column?': 1 }]);

      const result = await controller.check();
      expect(result.status).toBe('ok');
      expect(result.services.informer.status).toBe('up');
      expect(result.services.analytics.status).toBe('up');
      expect(result.services.db.status).toBe('up');
      expect(result.timestamp).toBeDefined();
    });
  });

  describe('check — degraded when service down', () => {
    it('should return degraded when informer is down', async () => {
      mockInformerGrpcService.Check.mockReturnValue(
        throwError(() => new Error('Connection refused')),
      );
      mockAnalyticsGrpcService.Check.mockReturnValue(of({ status: 'SERVING' }));
      mockDataSource.query.mockResolvedValue([{ '?column?': 1 }]);

      const result = await controller.check();
      expect(result.status).toBe('degraded');
      expect(result.services.informer.status).toBe('down');
      expect(result.services.analytics.status).toBe('up');
    });
  });

  describe('check — degraded when DB down', () => {
    it('should return degraded when database is unreachable', async () => {
      mockInformerGrpcService.Check.mockReturnValue(of({ status: 'SERVING' }));
      mockAnalyticsGrpcService.Check.mockReturnValue(of({ status: 'SERVING' }));
      mockDataSource.query.mockRejectedValue(new Error('ECONNREFUSED'));

      const result = await controller.check();
      expect(result.status).toBe('degraded');
      expect(result.services.db.status).toBe('down');
      expect(result.services.db.error).toBe('ECONNREFUSED');
    });
  });
});
