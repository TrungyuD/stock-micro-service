"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.GrpcClientModule = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const microservices_1 = require("@nestjs/microservices");
const path_1 = require("path");
let GrpcClientModule = class GrpcClientModule {
};
exports.GrpcClientModule = GrpcClientModule;
exports.GrpcClientModule = GrpcClientModule = __decorate([
    (0, common_1.Global)(),
    (0, common_1.Module)({
        imports: [
            microservices_1.ClientsModule.registerAsync([
                {
                    name: 'INFORMER_SERVICE',
                    imports: [config_1.ConfigModule],
                    useFactory: (config) => ({
                        transport: microservices_1.Transport.GRPC,
                        options: {
                            package: 'stock.informer.v1',
                            protoPath: (0, path_1.join)(__dirname, '..', '..', '..', 'protos', 'informer.proto'),
                            url: config.get('INFORMER_GRPC_URL', 'localhost:50051'),
                            loader: {
                                includeDirs: [(0, path_1.join)(__dirname, '..', '..', '..', 'protos')],
                            },
                        },
                    }),
                    inject: [config_1.ConfigService],
                },
                {
                    name: 'ANALYTICS_SERVICE',
                    imports: [config_1.ConfigModule],
                    useFactory: (config) => ({
                        transport: microservices_1.Transport.GRPC,
                        options: {
                            package: 'stock.analytics.v1',
                            protoPath: (0, path_1.join)(__dirname, '..', '..', '..', 'protos', 'analytics.proto'),
                            url: config.get('ANALYTICS_GRPC_URL', 'localhost:50052'),
                            loader: {
                                includeDirs: [(0, path_1.join)(__dirname, '..', '..', '..', 'protos')],
                            },
                        },
                    }),
                    inject: [config_1.ConfigService],
                },
            ]),
        ],
        exports: [microservices_1.ClientsModule],
    })
], GrpcClientModule);
//# sourceMappingURL=grpc-client.module.js.map