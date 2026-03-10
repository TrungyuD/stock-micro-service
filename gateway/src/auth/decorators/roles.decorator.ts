/**
 * roles.decorator.ts — Metadata decorator for role-based access control.
 * Usage: @Roles('admin') on controller methods.
 */
import { SetMetadata } from '@nestjs/common';

export const ROLES_KEY = 'roles';
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);
