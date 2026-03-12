import { Module, Global } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { ClientsModule, Transport } from '@nestjs/microservices';
import { join } from 'path';

/**
 * GrpcClientModule — registers gRPC client proxies for Informer and Analytics services.
 * Marked @Global so all feature modules can inject the clients without re-importing.
 *
 * INFORMER_SERVICE (port 50051): StockService, PriceService, FinancialService, HealthService
 * ANALYTICS_SERVICE (port 50052): TechnicalAnalysisService, FundamentalAnalysisService,
 *                                  ScreeningService, ScoringService, HealthService
 *
 * Both clients load multiple proto files via protoPath array and declare multiple
 * package namespaces via the package array. includeDirs resolves import paths like
 * "common/pagination.proto" correctly. keepCase: true preserves snake_case field names.
 *
 * Proto path resolution: resolves from __dirname (dist/grpc/) walking up to find protos/
 * at the repo or Docker root. Falls back to process.cwd()/protos/ for containerised builds.
 */

/** Resolve proto root: walk up from __dirname until we find a protos/ directory */
function resolveProtoRoot(): string {
  const fs = require('fs');
  // Try __dirname-relative first (dev: dist/grpc → ../../.. = repo root)
  const fromDirname = join(__dirname, '..', '..', '..', 'protos');
  if (fs.existsSync(fromDirname)) return fromDirname;
  // Docker: protos/ sits alongside dist/ at cwd
  const fromCwd = join(process.cwd(), 'protos');
  if (fs.existsSync(fromCwd)) return fromCwd;
  // Fallback — let proto-loader error with a clear path
  return fromDirname;
}

const PROTO_ROOT = resolveProtoRoot();
@Global()
@Module({
  imports: [
    ClientsModule.registerAsync([
      {
        name: 'INFORMER_SERVICE',
        imports: [ConfigModule],
        useFactory: (config: ConfigService) => ({
          transport: Transport.GRPC,
          options: {
            package: ['stock.informer.v1', 'stock.common'],
            protoPath: [
              join(PROTO_ROOT, 'informer', 'v1', 'stock.proto'),
              join(PROTO_ROOT, 'informer', 'v1', 'price.proto'),
              join(PROTO_ROOT, 'informer', 'v1', 'financial.proto'),
              join(PROTO_ROOT, 'health.proto'),
            ],
            url: config.get<string>('INFORMER_GRPC_URL', 'localhost:50051'),
            loader: {
              includeDirs: [PROTO_ROOT],
              keepCase: true,
              longs: Number,
            },
          },
        }),
        inject: [ConfigService],
      },
      {
        name: 'ANALYTICS_SERVICE',
        imports: [ConfigModule],
        useFactory: (config: ConfigService) => ({
          transport: Transport.GRPC,
          options: {
            package: ['stock.analyzer.v1', 'stock.common'],
            protoPath: [
              join(PROTO_ROOT, 'analyzer', 'v1', 'technical.proto'),
              join(PROTO_ROOT, 'analyzer', 'v1', 'fundamental.proto'),
              join(PROTO_ROOT, 'analyzer', 'v1', 'screening.proto'),
              join(PROTO_ROOT, 'analyzer', 'v1', 'scoring.proto'),
              join(PROTO_ROOT, 'health.proto'),
            ],
            url: config.get<string>('ANALYTICS_GRPC_URL', 'localhost:50052'),
            loader: {
              includeDirs: [PROTO_ROOT],
              keepCase: true,
              longs: Number,
            },
          },
        }),
        inject: [ConfigService],
      },
    ]),
  ],
  exports: [ClientsModule],
})
export class GrpcClientModule {}
