/**
 * database.module.ts — TypeORM configuration module for NestJS gateway.
 *
 * Reads DB credentials from ConfigService (populated from .env).
 * synchronize: false — schema is managed by init-db/01-schema.sql, not TypeORM.
 * autoLoadEntities: true — entities registered via forFeature() are auto-included.
 */
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        host: config.get<string>('DB_HOST', 'localhost'),
        port: config.get<number>('DB_PORT', 5433),
        username: config.get<string>('DB_USER', 'stock_user'),
        password: config.get<string>('DB_PASSWORD', ''),
        database: config.get<string>('DB_NAME', 'stock_db'),

        // Schema is managed by 01-schema.sql — never let TypeORM alter it
        synchronize: false,

        // Auto-discover entities registered via TypeOrmModule.forFeature()
        autoLoadEntities: true,

        // Log slow queries in development; suppress in production
        logging: config.get<string>('NODE_ENV') === 'development' ? ['query', 'error'] : ['error'],
        maxQueryExecutionTime: 1000, // warn if query > 1s
      }),
    }),
  ],
})
export class DatabaseModule {}
