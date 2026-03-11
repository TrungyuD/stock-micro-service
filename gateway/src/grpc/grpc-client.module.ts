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
 * Path resolution at runtime (NestJS compiles src/ → dist/ stripping src prefix):
 *   __dirname = gateway/dist/grpc/ → ../../.. = stock-micro-service/ → protos/
 */
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
              join(__dirname, '..', '..', '..', 'protos', 'informer', 'v1', 'stock.proto'),
              join(__dirname, '..', '..', '..', 'protos', 'informer', 'v1', 'price.proto'),
              join(__dirname, '..', '..', '..', 'protos', 'informer', 'v1', 'financial.proto'),
              join(__dirname, '..', '..', '..', 'protos', 'health.proto'),
            ],
            url: config.get<string>('INFORMER_GRPC_URL', 'localhost:50051'),
            loader: {
              includeDirs: [join(__dirname, '..', '..', '..', 'protos')],
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
              join(__dirname, '..', '..', '..', 'protos', 'analyzer', 'v1', 'technical.proto'),
              join(__dirname, '..', '..', '..', 'protos', 'analyzer', 'v1', 'fundamental.proto'),
              join(__dirname, '..', '..', '..', 'protos', 'analyzer', 'v1', 'screening.proto'),
              join(__dirname, '..', '..', '..', 'protos', 'analyzer', 'v1', 'scoring.proto'),
              join(__dirname, '..', '..', '..', 'protos', 'health.proto'),
            ],
            url: config.get<string>('ANALYTICS_GRPC_URL', 'localhost:50052'),
            loader: {
              includeDirs: [join(__dirname, '..', '..', '..', 'protos')],
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
