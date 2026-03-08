/**
 * health.module.ts — Module for health check endpoint.
 * Uses gRPC clients from GrpcClientModule (global) and DataSource from TypeORM.
 */
import { Module } from '@nestjs/common';
import { HealthController } from './health.controller';

@Module({
  controllers: [HealthController],
})
export class HealthModule {}
