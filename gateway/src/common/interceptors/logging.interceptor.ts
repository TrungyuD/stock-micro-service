/**
 * logging.interceptor.ts — Logs HTTP method, URL, and response time for every request.
 */
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable, tap } from 'rxjs';
import { Request } from 'express';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const req = context.switchToHttp().getRequest<Request>();
    const { method, url } = req;
    const start = Date.now();

    return next.handle().pipe(
      tap({
        next: () => {
          const elapsed = Date.now() - start;
          this.logger.log(`${method} ${url} — ${elapsed}ms`);
        },
        error: (err) => {
          const elapsed = Date.now() - start;
          this.logger.error(`${method} ${url} — ${elapsed}ms — ${err.message}`);
        },
      }),
    );
  }
}
