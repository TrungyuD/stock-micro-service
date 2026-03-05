-- =============================================================================
-- 02-seed.sql — Initial stock tickers (S&P 500 subset, top 20 US stocks)
-- Runs after 01-schema.sql (alphabetical ordering)
-- ON CONFLICT DO NOTHING makes this idempotent — safe to re-run
-- =============================================================================

INSERT INTO stocks (symbol, name, sector, industry, exchange) VALUES
('AAPL',  'Apple Inc.',                    'Technology',              'Consumer Electronics',  'NASDAQ'),
('MSFT',  'Microsoft Corporation',         'Technology',              'Software',              'NASDAQ'),
('GOOGL', 'Alphabet Inc.',                 'Technology',              'Internet Services',     'NASDAQ'),
('AMZN',  'Amazon.com Inc.',               'Consumer Cyclical',       'E-Commerce',            'NASDAQ'),
('META',  'Meta Platforms Inc.',           'Technology',              'Social Media',          'NASDAQ'),
('TSLA',  'Tesla Inc.',                    'Consumer Cyclical',       'Auto Manufacturers',    'NASDAQ'),
('NVDA',  'NVIDIA Corporation',            'Technology',              'Semiconductors',        'NASDAQ'),
('JPM',   'JPMorgan Chase & Co.',          'Financial Services',      'Banks',                 'NYSE'),
('V',     'Visa Inc.',                     'Financial Services',      'Credit Services',       'NYSE'),
('JNJ',   'Johnson & Johnson',             'Healthcare',              'Pharmaceuticals',       'NYSE'),
('WMT',   'Walmart Inc.',                  'Consumer Defensive',      'Retail',                'NYSE'),
('PG',    'Procter & Gamble Co.',          'Consumer Defensive',      'Household Products',    'NYSE'),
('MA',    'Mastercard Inc.',               'Financial Services',      'Credit Services',       'NYSE'),
('UNH',   'UnitedHealth Group Inc.',       'Healthcare',              'Health Plans',          'NYSE'),
('HD',    'Home Depot Inc.',               'Consumer Cyclical',       'Home Improvement',      'NYSE'),
('DIS',   'Walt Disney Co.',               'Communication Services',  'Entertainment',         'NYSE'),
('BAC',   'Bank of America Corp.',         'Financial Services',      'Banks',                 'NYSE'),
('XOM',   'Exxon Mobil Corp.',             'Energy',                  'Oil & Gas',             'NYSE'),
('KO',    'Coca-Cola Co.',                 'Consumer Defensive',      'Beverages',             'NYSE'),
('PFE',   'Pfizer Inc.',                   'Healthcare',              'Pharmaceuticals',       'NYSE')
ON CONFLICT (symbol) DO NOTHING;
