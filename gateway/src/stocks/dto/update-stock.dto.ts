/**
 * update-stock.dto.ts — Request body for updating an existing stock.
 * All fields optional (partial update).
 */
import { PartialType } from '@nestjs/swagger';
import { CreateStockDto } from './create-stock.dto';

export class UpdateStockDto extends PartialType(CreateStockDto) {}
