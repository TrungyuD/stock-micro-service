import { AnalyticsService } from './analytics.service';
export declare class AnalyticsController {
    private readonly analyticsService;
    constructor(analyticsService: AnalyticsService);
    getIndicators(symbol: string): {
        symbol: string;
        message: string;
    };
}
