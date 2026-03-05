/**
 * watchlist.entity.ts — TypeORM entity for the `watchlists` table.
 * A named list belonging to a user (user_id is a string UUID from auth layer).
 */
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
  Unique,
} from 'typeorm';
import { WatchlistItemEntity } from './watchlist-item.entity';

@Entity('watchlists')
@Unique(['userId', 'name'])
export class WatchlistEntity {
  @PrimaryGeneratedColumn()
  id: number;

  /** External user identifier (UUID string from auth service) */
  @Column({ type: 'varchar', length: 36, name: 'user_id' })
  userId: string;

  @Column({ type: 'varchar', length: 100 })
  name: string;

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ type: 'timestamptz' })
  updatedAt: Date;

  @OneToMany(() => WatchlistItemEntity, (item) => item.watchlist, { cascade: true })
  items: WatchlistItemEntity[];
}
