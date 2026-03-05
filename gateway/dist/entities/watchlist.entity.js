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
exports.WatchlistEntity = void 0;
const typeorm_1 = require("typeorm");
const watchlist_item_entity_1 = require("./watchlist-item.entity");
let WatchlistEntity = class WatchlistEntity {
};
exports.WatchlistEntity = WatchlistEntity;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)(),
    __metadata("design:type", Number)
], WatchlistEntity.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 36, name: 'user_id' }),
    __metadata("design:type", String)
], WatchlistEntity.prototype, "userId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'varchar', length: 100 }),
    __metadata("design:type", String)
], WatchlistEntity.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], WatchlistEntity.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.UpdateDateColumn)({ type: 'timestamptz' }),
    __metadata("design:type", Date)
], WatchlistEntity.prototype, "updatedAt", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => watchlist_item_entity_1.WatchlistItemEntity, (item) => item.watchlist, { cascade: true }),
    __metadata("design:type", Array)
], WatchlistEntity.prototype, "items", void 0);
exports.WatchlistEntity = WatchlistEntity = __decorate([
    (0, typeorm_1.Entity)('watchlists'),
    (0, typeorm_1.Unique)(['userId', 'name'])
], WatchlistEntity);
//# sourceMappingURL=watchlist.entity.js.map