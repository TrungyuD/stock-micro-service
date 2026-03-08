/**
 * grpc-exception.filter.ts — Maps gRPC status codes to HTTP status codes.
 * Catches gRPC errors thrown by client calls and returns proper HTTP responses.
 */
import {
  Catch,
  ExceptionFilter,
  ArgumentsHost,
  HttpStatus,
  HttpException,
  Logger,
} from '@nestjs/common';
import { Response } from 'express';

/** gRPC status code → HTTP status code mapping */
const GRPC_TO_HTTP: Record<number, number> = {
  0: HttpStatus.OK, // OK
  1: HttpStatus.INTERNAL_SERVER_ERROR, // CANCELLED
  2: HttpStatus.INTERNAL_SERVER_ERROR, // UNKNOWN
  3: HttpStatus.BAD_REQUEST, // INVALID_ARGUMENT
  4: HttpStatus.GATEWAY_TIMEOUT, // DEADLINE_EXCEEDED
  5: HttpStatus.NOT_FOUND, // NOT_FOUND
  6: HttpStatus.CONFLICT, // ALREADY_EXISTS
  7: HttpStatus.FORBIDDEN, // PERMISSION_DENIED
  8: HttpStatus.TOO_MANY_REQUESTS, // RESOURCE_EXHAUSTED
  9: HttpStatus.BAD_REQUEST, // FAILED_PRECONDITION
  10: HttpStatus.CONFLICT, // ABORTED
  11: HttpStatus.BAD_REQUEST, // OUT_OF_RANGE
  12: HttpStatus.NOT_IMPLEMENTED, // UNIMPLEMENTED
  13: HttpStatus.INTERNAL_SERVER_ERROR, // INTERNAL
  14: HttpStatus.SERVICE_UNAVAILABLE, // UNAVAILABLE
  15: HttpStatus.INTERNAL_SERVER_ERROR, // DATA_LOSS
  16: HttpStatus.UNAUTHORIZED, // UNAUTHENTICATED
};

@Catch()
export class GrpcExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(GrpcExceptionFilter.name);

  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    // Pass through NestJS HttpExceptions (validation errors, etc.)
    if (exception instanceof HttpException) {
      const status = exception.getStatus();
      const body = exception.getResponse();
      response.status(status).json(
        typeof body === 'string'
          ? { statusCode: status, message: body, timestamp: new Date().toISOString() }
          : { ...body, timestamp: new Date().toISOString() },
      );
      return;
    }

    // gRPC errors have a numeric `code` property
    const grpcCode = exception?.code ?? exception?.status ?? 2;
    const httpStatus = GRPC_TO_HTTP[grpcCode] ?? HttpStatus.INTERNAL_SERVER_ERROR;
    const message = exception?.details || exception?.message || 'Internal server error';

    this.logger.error(`gRPC error [code=${grpcCode}]: ${message}`, exception?.stack);

    response.status(httpStatus).json({
      statusCode: httpStatus,
      message,
      timestamp: new Date().toISOString(),
    });
  }
}
