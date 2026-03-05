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
exports.ValuationMetricEntity = void 0;
const typeorm_1 = require("typeorm");
const stock_entity_1 = require("./stock.entity");
let ValuationMetricEntity = class ValuationMetricEntity {
};
exports.ValuationMetricEntity = ValuationMetricEntity;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)(),
    __metadata("design:type", Number)
], ValuationMetricEntity.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'stock_id' }),
    __metadata("design:type", Number)
], ValuationMetricEntity.prototype, "stockId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'timestamptz', name: 'calculated_at', default: () => 'NOW()' }),
    __metadata("design:type", Date)
], ValuationMetricEntity.prototype, "calculatedAt", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'trailing_pe' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "trailingPe", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'forward_pe' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "forwardPe", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'price_to_book' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "priceToBook", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'peg_ratio' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "pegRatio", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'price_to_sales' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "priceToSales", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true, name: 'ev_to_ebitda' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "evToEbitda", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 8, scale: 4, nullable: true, name: 'dividend_yield' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "dividendYield", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 8, scale: 4, nullable: true, name: 'payout_ratio' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "payoutRatio", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 20, nullable: true, name: 'valuation_signal' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "valuationSignal", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 5, scale: 2, nullable: true, name: 'valuation_score' }),
    __metadata("design:type", Object)
], ValuationMetricEntity.prototype, "valuationScore", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], ValuationMetricEntity.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => stock_entity_1.StockEntity, (stock) => stock.valuationMetrics, { onDelete: 'CASCADE' }),
    (0, typeorm_1.JoinColumn)({ name: 'stock_id' }),
    __metadata("design:type", stock_entity_1.StockEntity)
], ValuationMetricEntity.prototype, "stock", void 0);
exports.ValuationMetricEntity = ValuationMetricEntity = __decorate([
    (0, typeorm_1.Entity)('valuation_metrics'),
    (0, typeorm_1.Unique)(['stockId', 'calculatedAt']),
    (0, typeorm_1.Index)('idx_valuation_stock', ['stockId', 'calculatedAt'])
], ValuationMetricEntity);
//# sourceMappingURL=valuation-metric.entity.js.map