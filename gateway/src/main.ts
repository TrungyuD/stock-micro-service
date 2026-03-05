import { NestFactory } from '@nestjs/core';
import { ValidationPipe, VersioningType } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Global API prefix and URI versioning: /api/v1/...
  app.setGlobalPrefix('api');
  app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });

  // CORS — allow frontend dev server and configurable origins
  app.enableCors({
    origin: process.env.CORS_ORIGINS?.split(',') ?? ['http://localhost:5300'],
    credentials: true,
  });

  // Global validation pipe — strips unknown fields, applies class-validator
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // Swagger / OpenAPI documentation
  const swaggerConfig = new DocumentBuilder()
    .setTitle('Stock Trading API Gateway')
    .setDescription('REST API gateway that proxies requests to gRPC microservices')
    .setVersion('1.0')
    .addTag('stocks', 'Stock price and market data')
    .addTag('analytics', 'Technical indicators and valuation metrics')
    .build();

  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env.GATEWAY_PORT ?? 5001;
  // Bind to 0.0.0.0 so the server is reachable inside containers and behind PM2.
  await app.listen(port, '0.0.0.0');

  console.log(`Gateway running on http://localhost:${port}/api/v1`);
  console.log(`Swagger UI:  http://localhost:${port}/api/docs`);
}

bootstrap();

