"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@nestjs/core");
const common_1 = require("@nestjs/common");
const swagger_1 = require("@nestjs/swagger");
const app_module_1 = require("./app.module");
async function bootstrap() {
    const app = await core_1.NestFactory.create(app_module_1.AppModule);
    app.setGlobalPrefix('api');
    app.enableVersioning({ type: common_1.VersioningType.URI, defaultVersion: '1' });
    app.enableCors({
        origin: process.env.CORS_ORIGINS?.split(',') ?? ['http://localhost:5300'],
        credentials: true,
    });
    app.useGlobalPipes(new common_1.ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
        transformOptions: { enableImplicitConversion: true },
    }));
    const swaggerConfig = new swagger_1.DocumentBuilder()
        .setTitle('Stock Trading API Gateway')
        .setDescription('REST API gateway that proxies requests to gRPC microservices')
        .setVersion('1.0')
        .addTag('stocks', 'Stock price and market data')
        .addTag('analytics', 'Technical indicators and valuation metrics')
        .build();
    const document = swagger_1.SwaggerModule.createDocument(app, swaggerConfig);
    swagger_1.SwaggerModule.setup('api/docs', app, document);
    const port = process.env.GATEWAY_PORT ?? 5001;
    await app.listen(port, '0.0.0.0');
    console.log(`Gateway running on http://localhost:${port}/api/v1`);
    console.log(`Swagger UI:  http://localhost:${port}/api/docs`);
}
bootstrap();
//# sourceMappingURL=main.js.map