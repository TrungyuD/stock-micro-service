/**
 * health.controller.ts — Health check endpoint that pings gRPC services and DB.
 * Returns aggregate health status of all connected services.
 * Uses HealthService (stock.common package) registered on both Informer and Analytics servers.
 * Method name changed from HealthCheck → Check per the new health.proto definition.
 */
import { Controller, Get, Inject, Logger, OnModuleInit } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { ClientGrpc } from '@nestjs/microservices';
import { lastValueFrom, Observable, timeout, catchError, of } from 'rxjs';
import { DataSource } from 'typeorm';

/** Matches health.proto HealthService (stock.common package) */
interface HealthGrpcService {
  Check(req: Record<string, never>): Observable<any>;
}

@ApiTags('health')
@Controller('health')
export class HealthController implements OnModuleInit {
  private readonly logger = new Logger(HealthController.name);
  private informerHealth: HealthGrpcService;
  private analyticsHealth: HealthGrpcService;

  constructor(
    @Inject('INFORMER_SERVICE') private readonly informerClient: ClientGrpc,
    @Inject('ANALYTICS_SERVICE') private readonly analyticsClient: ClientGrpc,
    private readonly dataSource: DataSource,
  ) {}

  onModuleInit() {
    // HealthService is registered under stock.common package on both servers
    this.informerHealth = this.informerClient.getService<HealthGrpcService>('HealthService');
    this.analyticsHealth = this.analyticsClient.getService<HealthGrpcService>('HealthService');
  }

  @Get()
  @ApiOperation({ summary: 'Health check — gateway + connected services' })
  @ApiResponse({ status: 200, description: 'Health status of all services' })
  async check() {
    const [informer, analytics, db] = await Promise.all([
      this.pingService('informer', this.informerHealth),
      this.pingService('analytics', this.analyticsHealth),
      this.pingDatabase(),
    ]);

    const allUp = informer.status === 'up' && analytics.status === 'up' && db.status === 'up';

    return {
      status: allUp ? 'ok' : 'degraded',
      timestamp: new Date().toISOString(),
      services: { informer, analytics, db },
    };
  }

  /** Ping a gRPC HealthService with a 3-second timeout */
  private async pingService(name: string, svc: HealthGrpcService) {
    try {
      const result = await lastValueFrom(
        svc.Check({}).pipe(
          timeout(3000),
          catchError((err) => of({ error: err.message })),
        ),
      );
      return result.error ? { status: 'down', error: result.error } : { status: 'up' };
    } catch (err: any) {
      this.logger.warn(`${name} health check failed: ${err.message}`);
      return { status: 'down', error: err.message };
    }
  }

  /** Ping PostgreSQL with a simple query */
  private async pingDatabase() {
    try {
      await this.dataSource.query('SELECT 1');
      return { status: 'up' };
    } catch (err: any) {
      this.logger.warn(`DB health check failed: ${err.message}`);
      return { status: 'down', error: err.message };
    }
  }
}
