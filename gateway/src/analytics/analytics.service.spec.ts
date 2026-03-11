import { Test, TestingModule } from '@nestjs/testing';
import { of } from 'rxjs';
import { AnalyticsService } from './analytics.service';

describe('AnalyticsService', () => {
  let service: AnalyticsService;

  // Mock for TechnicalAnalysisService
  const mockTechnicalGrpcService = {
    GetTechnicalIndicators: jest.fn(),
    GetMultipleIndicators: jest.fn(),
    GetIndicatorBatch: jest.fn(),
  };

  // Mock for FundamentalAnalysisService
  const mockFundamentalGrpcService = {
    GetValuationMetrics: jest.fn(),
    GetStockAnalysis: jest.fn(),
    CompareStocks: jest.fn(),
  };

  // Mock for ScreeningService
  const mockScreeningGrpcService = {
    ScreenStocks: jest.fn(),
    BatchAnalysis: jest.fn(),
    GetPresetScreens: jest.fn(),
    TriggerCalculation: jest.fn(),
  };

  // Mock for ScoringService
  const mockScoringGrpcService = {
    GetScore: jest.fn(),
    GetBatchScores: jest.fn(),
    GetRecommendation: jest.fn(),
  };

  const mockClient = {
    getService: jest.fn().mockImplementation((name: string) => {
      if (name === 'TechnicalAnalysisService') return mockTechnicalGrpcService;
      if (name === 'FundamentalAnalysisService') return mockFundamentalGrpcService;
      if (name === 'ScreeningService') return mockScreeningGrpcService;
      if (name === 'ScoringService') return mockScoringGrpcService;
      return {};
    }),
  };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AnalyticsService,
        { provide: 'ANALYTICS_SERVICE', useValue: mockClient },
      ],
    }).compile();

    service = module.get<AnalyticsService>(AnalyticsService);
    service.onModuleInit();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should initialize all four gRPC services on module init', () => {
    expect(mockClient.getService).toHaveBeenCalledWith('TechnicalAnalysisService');
    expect(mockClient.getService).toHaveBeenCalledWith('FundamentalAnalysisService');
    expect(mockClient.getService).toHaveBeenCalledWith('ScreeningService');
    expect(mockClient.getService).toHaveBeenCalledWith('ScoringService');
  });

  // --- Fundamental Analysis ---

  describe('getValuationMetrics', () => {
    it('should call FundamentalAnalysisService.GetValuationMetrics', async () => {
      const mockResponse = { metrics: { symbol: 'AAPL', trailing_pe: 25.5 } };
      mockFundamentalGrpcService.GetValuationMetrics.mockReturnValue(of(mockResponse));

      const result = await service.getValuationMetrics('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockFundamentalGrpcService.GetValuationMetrics).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });

  describe('getStockAnalysis', () => {
    it('should call FundamentalAnalysisService.GetStockAnalysis', async () => {
      const mockResponse = { analysis: { recommendation: 'Buy' } };
      mockFundamentalGrpcService.GetStockAnalysis.mockReturnValue(of(mockResponse));

      const result = await service.getStockAnalysis('AAPL', { includeRationale: true });
      expect(result).toEqual(mockResponse);
      expect(mockFundamentalGrpcService.GetStockAnalysis).toHaveBeenCalledWith({
        symbol: 'AAPL',
        include_rationale: true,
      });
    });

    it('should default include_rationale to false', async () => {
      mockFundamentalGrpcService.GetStockAnalysis.mockReturnValue(of({}));
      await service.getStockAnalysis('AAPL', {});
      expect(mockFundamentalGrpcService.GetStockAnalysis).toHaveBeenCalledWith({
        symbol: 'AAPL',
        include_rationale: false,
      });
    });
  });

  describe('compareStocks', () => {
    it('should call FundamentalAnalysisService.CompareStocks', async () => {
      const mockResponse = { comparisons: [], failed_symbols: [] };
      mockFundamentalGrpcService.CompareStocks.mockReturnValue(of(mockResponse));

      const result = await service.compareStocks(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
      expect(mockFundamentalGrpcService.CompareStocks).toHaveBeenCalledWith({ symbols: ['AAPL', 'MSFT'] });
    });
  });

  // --- Technical Analysis ---

  describe('getTechnicalIndicators', () => {
    it('should call TechnicalAnalysisService.GetTechnicalIndicators with timeframe default', async () => {
      const mockResponse = { indicators: { symbol: 'AAPL' } };
      mockTechnicalGrpcService.GetTechnicalIndicators.mockReturnValue(of(mockResponse));

      const result = await service.getTechnicalIndicators('AAPL', {});
      expect(result).toEqual(mockResponse);
      expect(mockTechnicalGrpcService.GetTechnicalIndicators).toHaveBeenCalledWith({
        symbol: 'AAPL',
        timeframe: '1d',
      });
    });
  });

  describe('getMultipleIndicators', () => {
    it('should call TechnicalAnalysisService.GetMultipleIndicators', async () => {
      const mockResponse = { symbol: 'AAPL', indicators: {} };
      mockTechnicalGrpcService.GetMultipleIndicators.mockReturnValue(of(mockResponse));

      const result = await service.getMultipleIndicators('AAPL', ['rsi', 'macd']);
      expect(result).toEqual(mockResponse);
      expect(mockTechnicalGrpcService.GetMultipleIndicators).toHaveBeenCalledWith({
        symbol: 'AAPL',
        indicator_names: ['rsi', 'macd'],
        timeframe: '1d',
      });
    });
  });

  describe('getIndicatorBatch', () => {
    it('should call TechnicalAnalysisService.GetIndicatorBatch', async () => {
      const mockResponse = { results: [], failed_symbols: [] };
      mockTechnicalGrpcService.GetIndicatorBatch.mockReturnValue(of(mockResponse));

      const result = await service.getIndicatorBatch(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
      expect(mockTechnicalGrpcService.GetIndicatorBatch).toHaveBeenCalledWith({
        symbols: ['AAPL', 'MSFT'],
        timeframe: '1d',
      });
    });
  });

  // --- Screening ---

  describe('screenStocks', () => {
    it('should call ScreeningService.ScreenStocks with criteria', async () => {
      const mockResponse = { stocks: [], total_matched: 0 };
      mockScreeningGrpcService.ScreenStocks.mockReturnValue(of(mockResponse));

      const result = await service.screenStocks({ maxPe: 25, limit: 10 });
      expect(result).toEqual(mockResponse);
      expect(mockScreeningGrpcService.ScreenStocks).toHaveBeenCalledWith(
        expect.objectContaining({
          criteria: expect.objectContaining({ max_pe: 25 }),
          limit: 10,
        }),
      );
    });
  });

  describe('batchAnalysis', () => {
    it('should call ScreeningService.BatchAnalysis', async () => {
      const mockResponse = { analyses: [], failed_symbols: [] };
      mockScreeningGrpcService.BatchAnalysis.mockReturnValue(of(mockResponse));

      const result = await service.batchAnalysis(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
      expect(mockScreeningGrpcService.BatchAnalysis).toHaveBeenCalledWith({ symbols: ['AAPL', 'MSFT'] });
    });
  });

  describe('getPresetScreens', () => {
    it('should call ScreeningService.GetPresetScreens', async () => {
      const mockResponse = { presets: [] };
      mockScreeningGrpcService.GetPresetScreens.mockReturnValue(of(mockResponse));

      const result = await service.getPresetScreens();
      expect(result).toEqual(mockResponse);
      expect(mockScreeningGrpcService.GetPresetScreens).toHaveBeenCalledWith({});
    });
  });

  // --- Scoring ---

  describe('getScore', () => {
    it('should call ScoringService.GetScore with symbol and optional strategy', async () => {
      const mockResponse = { score: { symbol: 'AAPL', overall_score: 72 } };
      mockScoringGrpcService.GetScore.mockReturnValue(of(mockResponse));

      const result = await service.getScore('AAPL', 'value');
      expect(result).toEqual(mockResponse);
      expect(mockScoringGrpcService.GetScore).toHaveBeenCalledWith({ symbol: 'AAPL', strategy: 'value' });
    });
  });

  describe('getBatchScores', () => {
    it('should call ScoringService.GetBatchScores', async () => {
      const mockResponse = { scores: [], failed_symbols: [] };
      mockScoringGrpcService.GetBatchScores.mockReturnValue(of(mockResponse));

      const result = await service.getBatchScores(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
      expect(mockScoringGrpcService.GetBatchScores).toHaveBeenCalledWith({
        symbols: ['AAPL', 'MSFT'],
        strategy: undefined,
      });
    });
  });

  describe('getRecommendation', () => {
    it('should call ScoringService.GetRecommendation', async () => {
      const mockResponse = { recommendation: { action: 'Buy', confidence: 80 } };
      mockScoringGrpcService.GetRecommendation.mockReturnValue(of(mockResponse));

      const result = await service.getRecommendation('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockScoringGrpcService.GetRecommendation).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });
});
