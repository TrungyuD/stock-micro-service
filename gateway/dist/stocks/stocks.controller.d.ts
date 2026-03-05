import { StocksService } from './stocks.service';
export declare class StocksController {
    private readonly stocksService;
    constructor(stocksService: StocksService);
    findAll(): {
        message: string;
    };
    findOne(symbol: string): {
        symbol: string;
        message: string;
    };
}
