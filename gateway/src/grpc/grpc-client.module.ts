import { Module, Global } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { ClientsModule, Transport } from '@nestjs/microservices';
import { join } from 'path';

/**
 * GrpcClientModule — registers gRPC client proxies for Informer and Analytics services.
 * Marked @Global so all feature modules can inject the clients without re-importing.
 * Proto files are resolved relative to __dirname so the path is correct regardless
 * of the CWD from which the process is started (dev, PM2, Docker, etc.).
 *
 * Package names match proto package declarations:
 *   - stock.informer.v1 (informer.proto)
 *   - stock.analytics.v1 (analytics.proto)
 * includeDirs allows proto imports (e.g., "common/types.proto") to resolve correctly.
 * keepCase: true preserves snake_case field names from proto (no auto camelCase).
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
            package: 'stock.informer.v1',
            protoPath: join(__dirname, '..', '..', '..', 'protos', 'informer.proto'),
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
            package: 'stock.analytics.v1',
            protoPath: join(__dirname, '..', '..', '..', 'protos', 'analytics.proto'),
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
