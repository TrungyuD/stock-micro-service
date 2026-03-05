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
exports.FinancialReportEntity = void 0;
const typeorm_1 = require("typeorm");
const stock_entity_1 = require("./stock.entity");
let FinancialReportEntity = class FinancialReportEntity {
};
exports.FinancialReportEntity = FinancialReportEntity;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)(),
    __metadata("design:type", Number)
], FinancialReportEntity.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'stock_id' }),
    __metadata("design:type", Number)
], FinancialReportEntity.prototype, "stockId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'date', name: 'report_date' }),
    __metadata("design:type", Date)
], FinancialReportEntity.prototype, "reportDate", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 20, name: 'report_type' }),
    __metadata("design:type", String)
], FinancialReportEntity.prototype, "reportType", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "revenue", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "grossProfit", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "operatingIncome", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "netIncome", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "eps", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "totalAssets", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "totalLiabilities", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "shareholdersEquity", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "bookValuePerShare", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "operatingCashFlow", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "freeCashFlow", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 18, scale: 2, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "capex", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'bigint', nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "sharesOutstanding", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "debtToEquity", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "currentRatio", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "roe", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 4, nullable: true }),
    __metadata("design:type", Object)
], FinancialReportEntity.prototype, "roa", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], FinancialReportEntity.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.UpdateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], FinancialReportEntity.prototype, "updatedAt", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => stock_entity_1.StockEntity, (stock) => stock.financialReports, { onDelete: 'CASCADE' }),
    (0, typeorm_1.JoinColumn)({ name: 'stock_id' }),
    __metadata("design:type", stock_entity_1.StockEntity)
], FinancialReportEntity.prototype, "stock", void 0);
exports.FinancialReportEntity = FinancialReportEntity = __decorate([
    (0, typeorm_1.Entity)('financial_reports'),
    (0, typeorm_1.Unique)(['stockId', 'reportDate', 'reportType']),
    (0, typeorm_1.Index)('idx_financial_reports_stock', ['stockId', 'reportDate'])
], FinancialReportEntity);
//# sourceMappingURL=financial-report.entity.js.map