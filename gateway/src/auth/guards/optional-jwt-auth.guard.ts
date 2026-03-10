/**
 * optional-jwt-auth.guard.ts — Guard that attaches user if JWT present,
 * but does NOT reject unauthenticated requests (returns null user instead).
 * Use for semi-public endpoints that behave differently for logged-in users.
 */
import { Injectable, ExecutionContext } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

@Injectable()
export class OptionalJwtAuthGuard extends AuthGuard('jwt') {
  handleRequest(_err: any, user: any) {
    // Return user if token valid, null otherwise (no throw)
    return user || null;
  }

  canActivate(context: ExecutionContext) {
    // Still run the JWT strategy, but don't fail on missing/invalid token
    return super.canActivate(context);
  }

  getRequest(context: ExecutionContext) {
    return context.switchToHttp().getRequest();
  }
}
