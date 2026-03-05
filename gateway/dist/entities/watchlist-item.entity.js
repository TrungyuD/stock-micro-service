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
exports.WatchlistItemEntity = void 0;
const typeorm_1 = require("typeorm");
const watchlist_entity_1 = require("./watchlist.entity");
const stock_entity_1 = require("./stock.entity");
let WatchlistItemEntity = class WatchlistItemEntity {
};
exports.WatchlistItemEntity = WatchlistItemEntity;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)(),
    __metadata("design:type", Number)
], WatchlistItemEntity.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'watchlist_id' }),
    __metadata("design:type", Number)
], WatchlistItemEntity.prototype, "watchlistId", void 0);
__decorate([
    (0, typeorm_1.Column)({ name: 'stock_id' }),
    __metadata("design:type", Number)
], WatchlistItemEntity.prototype, "stockId", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({ type: 'timestamptz', name: 'added_at' }),
    __metadata("design:type", Date)
], WatchlistItemEntity.prototype, "addedAt", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => watchlist_entity_1.WatchlistEntity, (watchlist) => watchlist.items, { onDelete: 'CASCADE' }),
    (0, typeorm_1.JoinColumn)({ name: 'watchlist_id' }),
    __metadata("design:type", watchlist_entity_1.WatchlistEntity)
], WatchlistItemEntity.prototype, "watchlist", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => stock_entity_1.StockEntity, (stock) => stock.watchlistItems, { onDelete: 'CASCADE' }),
    (0, typeorm_1.JoinColumn)({ name: 'stock_id' }),
    __metadata("design:type", stock_entity_1.StockEntity)
], WatchlistItemEntity.prototype, "stock", void 0);
exports.WatchlistItemEntity = WatchlistItemEntity = __decorate([
    (0, typeorm_1.Entity)('watchlist_items'),
    (0, typeorm_1.Unique)(['watchlistId', 'stockId']),
    (0, typeorm_1.Index)('idx_watchlist_items_watchlist', ['watchlistId'])
], WatchlistItemEntity);
//# sourceMappingURL=watchlist-item.entity.js.map