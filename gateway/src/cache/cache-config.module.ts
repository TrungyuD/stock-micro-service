/**
 * cache-config.module.ts — Global cache module with Redis store.
 * Falls back to in-memory cache when Redis is unavailable.
 */
import { Module } from '@nestjs/common';
import { CacheModule } from '@nestjs/cache-manager';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { redisStore } from 'cache-manager-redis-yet';

@Module({
  imports: [
    CacheModule.registerAsync({
      isGlobal: true,
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: async (config: ConfigService) => {
        const redisHost = config.get<string>('REDIS_HOST');
        const redisPort = config.get<number>('REDIS_PORT');
        const redisPassword = config.get<string>('REDIS_PASSWORD');

        // Only use Redis if host is configured
        if (redisHost) {
          try {
            const store = await redisStore({
              socket: { host: redisHost, port: redisPort || 6379 },
              password: redisPassword,
              ttl: 60_000, // default 60s
            });
            console.log(`Cache: connected to Redis at ${redisHost}:${redisPort || 6379}`);
            return { store };
          } catch (err) {
            console.warn('Cache: Redis unavailable, falling back to in-memory', err);
          }
        }

        // In-memory fallback
        console.log('Cache: using in-memory store');
        return { ttl: 60_000 };
      },
    }),
  ],
})
export class CacheConfigModule {}
