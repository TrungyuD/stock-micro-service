import { HttpException, HttpStatus } from '@nestjs/common';
import { GrpcExceptionFilter } from './grpc-exception.filter';

describe('GrpcExceptionFilter', () => {
  let filter: GrpcExceptionFilter;
  let mockResponse: any;
  let mockHost: any;

  beforeEach(() => {
    filter = new GrpcExceptionFilter();
    mockResponse = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
    };
    mockHost = {
      switchToHttp: () => ({
        getResponse: () => mockResponse,
      }),
    };
  });

  it('should pass through HttpException', () => {
    const exception = new HttpException('Bad Request', HttpStatus.BAD_REQUEST);
    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.BAD_REQUEST);
  });

  it('should map gRPC NOT_FOUND (5) to HTTP 404', () => {
    const exception = { code: 5, details: 'Symbol not found' };
    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.NOT_FOUND);
    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        statusCode: HttpStatus.NOT_FOUND,
        message: 'Symbol not found',
      }),
    );
  });

  it('should map gRPC INVALID_ARGUMENT (3) to HTTP 400', () => {
    const exception = { code: 3, details: 'Invalid symbol' };
    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.BAD_REQUEST);
  });

  it('should map gRPC INTERNAL (13) to HTTP 500', () => {
    const exception = { code: 13, details: 'Internal error' };
    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.INTERNAL_SERVER_ERROR);
  });

  it('should map gRPC UNAVAILABLE (14) to HTTP 503', () => {
    const exception = { code: 14, details: 'Service unavailable' };
    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.SERVICE_UNAVAILABLE);
  });

  it('should map gRPC PERMISSION_DENIED (7) to HTTP 403', () => {
    const exception = { code: 7, details: 'Forbidden' };
    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.FORBIDDEN);
  });

  it('should default unknown codes to HTTP 500', () => {
    const exception = { code: 999, details: 'Unknown error' };
    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.INTERNAL_SERVER_ERROR);
  });

  it('should handle exception with message fallback', () => {
    const exception = { code: 2, message: 'Something went wrong' };
    filter.catch(exception, mockHost as any);

    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Something went wrong',
      }),
    );
  });
});
