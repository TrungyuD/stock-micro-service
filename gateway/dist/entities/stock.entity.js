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
exports.StockEntity = void 0;
const typeorm_1 = require("typeorm");
const ohlcv_entity_1 = require("./ohlcv.entity");
const financial_report_entity_1 = require("./financial-report.entity");
const indicator_entity_1 = require("./indicator.entity");
const valuation_metric_entity_1 = require("./valuation-metric.entity");
const watchlist_item_entity_1 = require("./watchlist-item.entity");
let StockEntity = class StockEntity {
};
exports.StockEntity = StockEntity;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)(),
    __metadata("design:type", Number)
], StockEntity.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 10, unique: true }),
    (0, typeorm_1.Index)('idx_stocks_symbol'),
    __metadata("design:type", String)
], StockEntity.prototype, "symbol", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 255 }),
    __metadata("design:type", String)
], StockEntity.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 100, nullable: true }),
    __metadata("design:type", Object)
], StockEntity.prototype, "sector", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 100, nullable: true }),
    __metadata("design:type", Object)
], StockEntity.prototype, "industry", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 50, nullable: true }),
    __metadata("design:type", Object)
], StockEntity.prototype, "exchange", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 50, default: 'US' }),
    __metadata("design:type", String)
], StockEntity.prototype, "country", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 10, default: 'USD' }),
    __metadata("design:type", String)
], StockEntity.prototype, "currency", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'bigint', nullable: true }),
    __metadata("design:type", Object)
], StockEntity.prototype, "marketCap", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'text', nullable: true }),
    __metadata("design:type", Object)
], StockEntity.prototype, "description", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 255, nullable: true }),
    __metadata("design:type", Object)
], StockEntity.prototype, "website", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'boolean', default: true }),
    __metadata("design:type", Boolean)
], StockEntity.prototype, "isActive", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], StockEntity.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.UpdateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], StockEntity.prototype, "updatedAt", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => ohlcv_entity_1.OhlcvEntity, (ohlcv) => ohlcv.stock),
    __metadata("design:type", Array)
], StockEntity.prototype, "ohlcv", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => financial_report_entity_1.FinancialReportEntity, (report) => report.stock),
    __metadata("design:type", Array)
], StockEntity.prototype, "financialReports", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => indicator_entity_1.IndicatorEntity, (indicator) => indicator.stock),
    __metadata("design:type", Array)
], StockEntity.prototype, "indicators", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => valuation_metric_entity_1.ValuationMetricEntity, (metric) => metric.stock),
    __metadata("design:type", Array)
], StockEntity.prototype, "valuationMetrics", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => watchlist_item_entity_1.WatchlistItemEntity, (item) => item.stock),
    __metadata("design:type", Array)
], StockEntity.prototype, "watchlistItems", void 0);
exports.StockEntity = StockEntity = __decorate([
    (0, typeorm_1.Entity)('stocks'),
    (0, typeorm_1.Index)('idx_stocks_sector', ['sector']),
    (0, typeorm_1.Index)('idx_stocks_exchange', ['exchange'])
], StockEntity);
//# sourceMappingURL=stock.entity.js.map