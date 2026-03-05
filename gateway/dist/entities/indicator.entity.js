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
exports.IndicatorEntity = void 0;
const typeorm_1 = require("typeorm");
const stock_entity_1 = require("./stock.entity");
let IndicatorEntity = class IndicatorEntity {
};
exports.IndicatorEntity = IndicatorEntity;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)(),
    __metadata("design:type", Number)
], IndicatorEntity.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'stock_id' }),
    __metadata("design:type", Number)
], IndicatorEntity.prototype, "stockId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], IndicatorEntity.prototype, "time", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 6, scale: 2, nullable: true, name: 'rsi_14' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "rsi14", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'sma_20' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "sma20", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'sma_50' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "sma50", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'sma_200' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "sma200", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'ema_20' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "ema20", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'ema_50' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "ema50", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'macd_line' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "macdLine", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'macd_signal' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "macdSignal", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'macd_histogram' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "macdHistogram", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'bb_upper' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "bbUpper", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'bb_middle' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "bbMiddle", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 12, scale: 4, nullable: true, name: 'bb_lower' }),
    __metadata("design:type", Object)
], IndicatorEntity.prototype, "bbLower", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], IndicatorEntity.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => stock_entity_1.StockEntity, (stock) => stock.indicators, { onDelete: 'CASCADE' }),
    (0, typeorm_1.JoinColumn)({ name: 'stock_id' }),
    __metadata("design:type", stock_entity_1.StockEntity)
], IndicatorEntity.prototype, "stock", void 0);
exports.IndicatorEntity = IndicatorEntity = __decorate([
    (0, typeorm_1.Entity)('indicators'),
    (0, typeorm_1.Unique)(['stockId', 'time']),
    (0, typeorm_1.Index)('idx_indicators_stock_time', ['stockId', 'time'])
], IndicatorEntity);
//# sourceMappingURL=indicator.entity.js.map