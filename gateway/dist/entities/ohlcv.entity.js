"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.OhlcvEntity = void 0;
const typeorm_1 = require("typeorm");
const stock_entity_1 = require("./stock.entity");
let OhlcvEntity = class OhlcvEntity {
};
exports.OhlcvEntity = OhlcvEntity;
__decorate([
    (0, typeorm_1.PrimaryColumn)({ type: 'timestamptz', name: 'time' }),
    __metadata("design:type", Date)
], OhlcvEntity.prototype, "time", void 0);
__decorate([
    (0, typeorm_1.PrimaryColumn)({ type: 'integer', name: 'stock_id' }),
    __metadata("design:type", Number)
], OhlcvEntity.prototype, "stockId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4 }),
    __metadata("design:type", Number)
], OhlcvEntity.prototype, "open", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4 }),
    __metadata("design:type", Number)
], OhlcvEntity.prototype, "high", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4 }),
    __metadata("design:type", Number)
], OhlcvEntity.prototype, "low", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4 }),
    __metadata("design:type", Number)
], OhlcvEntity.prototype, "close", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'bigint' }),
    __metadata("design:type", Number)
], OhlcvEntity.prototype, "volume", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true }),
    __metadata("design:type", Object)
], OhlcvEntity.prototype, "adjustedClose", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => stock_entity_1.StockEntity, (stock) => stock.ohlcv, { onDelete: 'CASCADE' }),
    (0, typeorm_1.JoinColumn)({ name: 'stock_id' }),
    __metadata("design:type", stock_entity_1.StockEntity)
], OhlcvEntity.prototype, "stock", void 0);
exports.OhlcvEntity = OhlcvEntity = __decorate([
    (0, typeorm_1.Entity)('ohlcv'),
    (0, typeorm_1.Index)('idx_ohlcv_stock_time', ['stockId', 'time'])
], OhlcvEntity);
//# sourceMappingURL=ohlcv.entity.js.map