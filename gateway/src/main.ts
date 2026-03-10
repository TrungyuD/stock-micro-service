/**
 * main.ts — NestJS bootstrap with Swagger, CORS, global validation,
 * gRPC exception filter, and request logging interceptor.
 */
import { NestFactory } from '@nestjs/core';
import { ValidationPipe, VersioningType } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import cookieParser from 'cookie-parser';
import { AppModule } from './app.module';
import { GrpcExceptionFilter } from './common/filters/grpc-exception.filter';
import { LoggingInterceptor } from './common/interceptors/logging.interceptor';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Cookie parser — needed for httpOnly refresh token cookies
  app.use(cookieParser());

  // Global API prefix and URI versioning: /api/v1/...
  app.setGlobalPrefix('api');
  app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });

  // CORS — allow all origins in development
  app.enableCors({
    origin: true,
    methods: 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
    allowedHeaders: 'Content-Type,Authorization,Accept',
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

  // Global exception filter — maps gRPC errors to HTTP status codes
  app.useGlobalFilters(new GrpcExceptionFilter());

  // Global logging interceptor — logs method, URL, response time
  app.useGlobalInterceptors(new LoggingInterceptor());

  // Swagger / OpenAPI documentation
  const swaggerConfig = new DocumentBuilder()
    .setTitle('Stock Trading API Gateway')
    .setDescription('REST API gateway that proxies requests to gRPC microservices')
    .setVersion('1.0')
    .addBearerAuth()
    .addTag('auth', 'Authentication endpoints')
    .addTag('health', 'Service health checks')
    .addTag('stocks', 'Stock price and market data')
    .addTag('analytics', 'Technical indicators and valuation metrics')
    .addTag('watchlists', 'Watchlist management')
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
