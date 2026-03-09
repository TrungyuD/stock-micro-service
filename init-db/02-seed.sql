-- =============================================================================
-- 02-seed.sql — Stock tickers seed data (~200 stocks: US + VN)
-- Runs after 01-schema.sql (alphabetical ordering)
-- ON CONFLICT DO NOTHING makes this idempotent — safe to re-run
-- =============================================================================

-- =============================================
-- US STOCKS (~100) — country='US', currency='USD'
-- =============================================

-- Technology
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('AAPL',  'Apple Inc.',                    'Technology',    'Consumer Electronics',  'NASDAQ', 'US', 'USD'),
('MSFT',  'Microsoft Corporation',         'Technology',    'Software',              'NASDAQ', 'US', 'USD'),
('GOOGL', 'Alphabet Inc.',                 'Technology',    'Internet Services',     'NASDAQ', 'US', 'USD'),
('META',  'Meta Platforms Inc.',           'Technology',    'Social Media',          'NASDAQ', 'US', 'USD'),
('NVDA',  'NVIDIA Corporation',            'Technology',    'Semiconductors',        'NASDAQ', 'US', 'USD'),
('INTC',  'Intel Corporation',             'Technology',    'Semiconductors',        'NASDAQ', 'US', 'USD'),
('AMD',   'Advanced Micro Devices Inc.',   'Technology',    'Semiconductors',        'NASDAQ', 'US', 'USD'),
('QCOM',  'Qualcomm Inc.',                'Technology',    'Semiconductors',        'NASDAQ', 'US', 'USD'),
('CRM',   'Salesforce Inc.',              'Technology',    'Software',              'NYSE',   'US', 'USD'),
('ADBE',  'Adobe Inc.',                   'Technology',    'Software',              'NASDAQ', 'US', 'USD'),
('NFLX',  'Netflix Inc.',                 'Technology',    'Entertainment',         'NASDAQ', 'US', 'USD'),
('CSCO',  'Cisco Systems Inc.',           'Technology',    'Networking',            'NASDAQ', 'US', 'USD'),
('ORCL',  'Oracle Corporation',           'Technology',    'Software',              'NYSE',   'US', 'USD'),
('IBM',   'IBM Corporation',              'Technology',    'IT Services',           'NYSE',   'US', 'USD'),
('NOW',   'ServiceNow Inc.',              'Technology',    'Software',              'NYSE',   'US', 'USD'),
('UBER',  'Uber Technologies Inc.',       'Technology',    'Transportation Tech',   'NYSE',   'US', 'USD'),
('AMAT',  'Applied Materials Inc.',       'Technology',    'Semiconductors',        'NASDAQ', 'US', 'USD'),
('ASML',  'ASML Holding NV',             'Technology',    'Semiconductors',        'NASDAQ', 'US', 'USD'),
('AVGO',  'Broadcom Inc.',               'Technology',    'Semiconductors',        'NASDAQ', 'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Financial Services
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('JPM',   'JPMorgan Chase & Co.',          'Financial Services', 'Banks',              'NYSE',   'US', 'USD'),
('V',     'Visa Inc.',                     'Financial Services', 'Credit Services',    'NYSE',   'US', 'USD'),
('MA',    'Mastercard Inc.',               'Financial Services', 'Credit Services',    'NYSE',   'US', 'USD'),
('BAC',   'Bank of America Corp.',         'Financial Services', 'Banks',              'NYSE',   'US', 'USD'),
('GS',    'Goldman Sachs Group Inc.',      'Financial Services', 'Investment Banking', 'NYSE',   'US', 'USD'),
('WFC',   'Wells Fargo & Co.',            'Financial Services', 'Banks',              'NYSE',   'US', 'USD'),
('USB',   'U.S. Bancorp',                 'Financial Services', 'Banks',              'NYSE',   'US', 'USD'),
('PNC',   'PNC Financial Services',       'Financial Services', 'Banks',              'NYSE',   'US', 'USD'),
('BLK',   'BlackRock Inc.',               'Financial Services', 'Asset Management',   'NYSE',   'US', 'USD'),
('SCHW',  'Charles Schwab Corp.',         'Financial Services', 'Brokerage',          'NYSE',   'US', 'USD'),
('AXP',   'American Express Co.',         'Financial Services', 'Credit Services',    'NYSE',   'US', 'USD'),
('CME',   'CME Group Inc.',               'Financial Services', 'Exchanges',          'NASDAQ', 'US', 'USD'),
('ICE',   'Intercontinental Exchange',    'Financial Services', 'Exchanges',          'NYSE',   'US', 'USD'),
('PYPL',  'PayPal Holdings Inc.',         'Financial Services', 'Digital Payments',   'NASDAQ', 'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Healthcare
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('JNJ',   'Johnson & Johnson',             'Healthcare', 'Pharmaceuticals',    'NYSE',   'US', 'USD'),
('UNH',   'UnitedHealth Group Inc.',       'Healthcare', 'Health Plans',        'NYSE',   'US', 'USD'),
('PFE',   'Pfizer Inc.',                   'Healthcare', 'Pharmaceuticals',    'NYSE',   'US', 'USD'),
('ABBV',  'AbbVie Inc.',                  'Healthcare', 'Pharmaceuticals',    'NYSE',   'US', 'USD'),
('LLY',   'Eli Lilly & Co.',             'Healthcare', 'Pharmaceuticals',    'NYSE',   'US', 'USD'),
('MRK',   'Merck & Co. Inc.',            'Healthcare', 'Pharmaceuticals',    'NYSE',   'US', 'USD'),
('GILD',  'Gilead Sciences Inc.',         'Healthcare', 'Biopharmaceuticals', 'NASDAQ', 'US', 'USD'),
('AMGN',  'Amgen Inc.',                  'Healthcare', 'Biotech',            'NASDAQ', 'US', 'USD'),
('CVS',   'CVS Health Corp.',            'Healthcare', 'Pharmacy',           'NYSE',   'US', 'USD'),
('ISRG',  'Intuitive Surgical Inc.',     'Healthcare', 'Medical Devices',    'NASDAQ', 'US', 'USD'),
('REGN',  'Regeneron Pharmaceuticals',   'Healthcare', 'Biopharmaceuticals', 'NASDAQ', 'US', 'USD'),
('VRTX',  'Vertex Pharmaceuticals',      'Healthcare', 'Biopharmaceuticals', 'NASDAQ', 'US', 'USD'),
('BMY',   'Bristol-Myers Squibb Co.',    'Healthcare', 'Pharmaceuticals',    'NYSE',   'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Consumer Cyclical
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('AMZN',  'Amazon.com Inc.',              'Consumer Cyclical', 'E-Commerce',         'NASDAQ', 'US', 'USD'),
('TSLA',  'Tesla Inc.',                   'Consumer Cyclical', 'Auto Manufacturers',  'NASDAQ', 'US', 'USD'),
('HD',    'Home Depot Inc.',              'Consumer Cyclical', 'Home Improvement',    'NYSE',   'US', 'USD'),
('NKE',   'Nike Inc.',                   'Consumer Cyclical', 'Apparel',             'NYSE',   'US', 'USD'),
('MCD',   'McDonalds Corp.',             'Consumer Cyclical', 'Restaurants',         'NYSE',   'US', 'USD'),
('SBUX',  'Starbucks Corp.',             'Consumer Cyclical', 'Restaurants',         'NASDAQ', 'US', 'USD'),
('COST',  'Costco Wholesale Corp.',      'Consumer Cyclical', 'Retail',              'NASDAQ', 'US', 'USD'),
('TJX',   'TJX Companies Inc.',          'Consumer Cyclical', 'Retail',              'NYSE',   'US', 'USD'),
('LULU',  'Lululemon Athletica',         'Consumer Cyclical', 'Apparel',             'NASDAQ', 'US', 'USD'),
('LOW',   'Lowes Companies Inc.',        'Consumer Cyclical', 'Home Improvement',    'NYSE',   'US', 'USD'),
('TGT',   'Target Corp.',               'Consumer Cyclical', 'Retail',              'NYSE',   'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Consumer Defensive
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('WMT',   'Walmart Inc.',                 'Consumer Defensive', 'Retail',              'NYSE',   'US', 'USD'),
('PG',    'Procter & Gamble Co.',         'Consumer Defensive', 'Household Products',  'NYSE',   'US', 'USD'),
('KO',    'Coca-Cola Co.',               'Consumer Defensive', 'Beverages',           'NYSE',   'US', 'USD'),
('PEP',   'PepsiCo Inc.',               'Consumer Defensive', 'Beverages',           'NASDAQ', 'US', 'USD'),
('MO',    'Altria Group Inc.',           'Consumer Defensive', 'Tobacco',             'NYSE',   'US', 'USD'),
('PM',    'Philip Morris International', 'Consumer Defensive', 'Tobacco',             'NYSE',   'US', 'USD'),
('CL',    'Colgate-Palmolive Co.',       'Consumer Defensive', 'Consumer Products',   'NYSE',   'US', 'USD'),
('MDLZ',  'Mondelez International',      'Consumer Defensive', 'Food',                'NASDAQ', 'US', 'USD'),
('KHC',   'Kraft Heinz Co.',            'Consumer Defensive', 'Food',                'NASDAQ', 'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Communication Services
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('DIS',   'Walt Disney Co.',              'Communication Services', 'Entertainment',  'NYSE',   'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Industrials
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('BA',    'Boeing Co.',                   'Industrials', 'Aerospace',             'NYSE', 'US', 'USD'),
('CAT',   'Caterpillar Inc.',            'Industrials', 'Heavy Equipment',       'NYSE', 'US', 'USD'),
('GE',    'General Electric Co.',        'Industrials', 'Conglomerate',          'NYSE', 'US', 'USD'),
('LMT',   'Lockheed Martin Corp.',       'Industrials', 'Defense',               'NYSE', 'US', 'USD'),
('RTX',   'RTX Corporation',             'Industrials', 'Aerospace',             'NYSE', 'US', 'USD'),
('UPS',   'United Parcel Service Inc.',  'Industrials', 'Logistics',             'NYSE', 'US', 'USD'),
('FDX',   'FedEx Corp.',                'Industrials', 'Logistics',             'NYSE', 'US', 'USD'),
('HON',   'Honeywell International',    'Industrials', 'Conglomerate',          'NASDAQ', 'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Energy
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('XOM',   'Exxon Mobil Corp.',            'Energy', 'Oil & Gas',          'NYSE', 'US', 'USD'),
('CVX',   'Chevron Corp.',               'Energy', 'Oil & Gas',          'NYSE', 'US', 'USD'),
('COP',   'ConocoPhillips',              'Energy', 'Oil & Gas',          'NYSE', 'US', 'USD'),
('SLB',   'Schlumberger NV',             'Energy', 'Oilfield Services',  'NYSE', 'US', 'USD'),
('EOG',   'EOG Resources Inc.',          'Energy', 'Oil & Gas',          'NYSE', 'US', 'USD'),
('OXY',   'Occidental Petroleum',        'Energy', 'Oil & Gas',          'NYSE', 'US', 'USD'),
('PSX',   'Phillips 66',                 'Energy', 'Refining',           'NYSE', 'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Utilities
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('NEE',   'NextEra Energy Inc.',          'Utilities', 'Electric Utility', 'NYSE',   'US', 'USD'),
('DUK',   'Duke Energy Corp.',           'Utilities', 'Electric Utility', 'NYSE',   'US', 'USD'),
('SO',    'Southern Company',            'Utilities', 'Electric Utility', 'NYSE',   'US', 'USD'),
('AEP',   'American Electric Power',     'Utilities', 'Electric Utility', 'NASDAQ', 'US', 'USD'),
('EXC',   'Exelon Corp.',               'Utilities', 'Electric Utility', 'NASDAQ', 'US', 'USD'),
('WEC',   'WEC Energy Group',           'Utilities', 'Electric Utility', 'NYSE',   'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Real Estate
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('PLD',   'Prologis Inc.',               'Real Estate', 'Industrial REITs',  'NYSE',   'US', 'USD'),
('EQIX',  'Equinix Inc.',               'Real Estate', 'Data Center REITs', 'NASDAQ', 'US', 'USD'),
('PSA',   'Public Storage',             'Real Estate', 'Storage REITs',     'NYSE',   'US', 'USD'),
('VICI',  'VICI Properties Inc.',       'Real Estate', 'Gaming REITs',      'NYSE',   'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Materials
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('NEM',   'Newmont Corp.',               'Materials', 'Gold Mining',       'NYSE', 'US', 'USD'),
('FCX',   'Freeport-McMoRan Inc.',       'Materials', 'Copper Mining',     'NYSE', 'US', 'USD'),
('APD',   'Air Products & Chemicals',    'Materials', 'Industrial Gases',  'NYSE', 'US', 'USD'),
('LIN',   'Linde PLC',                  'Materials', 'Industrial Gases',  'NASDAQ', 'US', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- =============================================
-- VN STOCKS (~100) — country='VN', currency='VND'
-- =============================================

-- Banking
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('VCB.VN', 'Vietcombank',                     'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('BID.VN', 'BIDV',                            'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('ACB.VN', 'Asia Commercial Bank',            'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('MBB.VN', 'Military Commercial Bank',        'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('CTG.VN', 'VietinBank',                      'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('SHB.VN', 'Saigon-Hanoi Bank',              'Financial Services', 'Banks',          'HNX',  'VN', 'VND'),
('TCB.VN', 'Techcombank',                     'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('EIB.VN', 'Eximbank',                        'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('STB.VN', 'Sacombank',                       'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('HDB.VN', 'HDBank',                          'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('TPB.VN', 'TPBank',                          'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('VPB.VN', 'VPBank',                          'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('LPB.VN', 'LienVietPostBank',               'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('SSB.VN', 'SeABank',                         'Financial Services', 'Banks',          'HOSE', 'VN', 'VND'),
('OCB.VN', 'Orient Commercial Bank',          'Financial Services', 'Banks',          'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Real Estate
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('VIC.VN', 'Vingroup JSC',                    'Real Estate', 'Conglomerate',     'HOSE', 'VN', 'VND'),
('VRE.VN', 'Vincom Retail',                   'Real Estate', 'Commercial REITs', 'HOSE', 'VN', 'VND'),
('PDR.VN', 'Phat Dat Real Estate',            'Real Estate', 'Residential',      'HOSE', 'VN', 'VND'),
('NVL.VN', 'Novaland Group',                  'Real Estate', 'Residential',      'HOSE', 'VN', 'VND'),
('DIG.VN', 'DIC Group JSC',                   'Real Estate', 'Diversified',      'HOSE', 'VN', 'VND'),
('KDH.VN', 'Khang Dien House',               'Real Estate', 'Residential',      'HOSE', 'VN', 'VND'),
('DXG.VN', 'Dat Xanh Group',                 'Real Estate', 'Residential',      'HOSE', 'VN', 'VND'),
('HDG.VN', 'Ha Do Group',                     'Real Estate', 'Diversified',      'HOSE', 'VN', 'VND'),
('NLG.VN', 'Nam Long Group',                  'Real Estate', 'Residential',      'HOSE', 'VN', 'VND'),
('IJC.VN', 'Becamex IJC',                     'Real Estate', 'Industrial Parks', 'HOSE', 'VN', 'VND'),
('CEO.VN', 'CEO Group JSC',                   'Real Estate', 'Diversified',      'HNX',  'VN', 'VND'),
('DPG.VN', 'Dat Phuong Group',               'Real Estate', 'Construction',     'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Food & Beverage
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('VNM.VN', 'Vinamilk',                        'Consumer Defensive', 'Dairy',          'HOSE', 'VN', 'VND'),
('SAB.VN', 'Sabeco',                           'Consumer Defensive', 'Beverages',      'HOSE', 'VN', 'VND'),
('MSN.VN', 'Masan Group',                     'Consumer Defensive', 'Diversified',    'HOSE', 'VN', 'VND'),
('MCH.VN', 'Masan Consumer',                  'Consumer Defensive', 'Consumer Goods', 'HOSE', 'VN', 'VND'),
('QNS.VN', 'Quang Ngai Sugar',               'Consumer Defensive', 'Food',           'HOSE', 'VN', 'VND'),
('KDC.VN', 'Kido Group',                      'Consumer Defensive', 'Food',           'HOSE', 'VN', 'VND'),
('SBT.VN', 'TTC Sugar',                       'Consumer Defensive', 'Food',           'HOSE', 'VN', 'VND'),
('ANV.VN', 'Nam Viet Corp',                   'Consumer Defensive', 'Seafood',        'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Steel & Manufacturing
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('HPG.VN', 'Hoa Phat Group',                  'Materials', 'Steel',             'HOSE', 'VN', 'VND'),
('HSG.VN', 'Hoa Sen Group',                   'Materials', 'Steel',             'HOSE', 'VN', 'VND'),
('NKG.VN', 'Nam Kim Steel',                   'Materials', 'Steel',             'HOSE', 'VN', 'VND'),
('SMC.VN', 'SMC Trading',                     'Materials', 'Steel',             'HOSE', 'VN', 'VND'),
('TLH.VN', 'Thep Lien Hoa',                  'Materials', 'Steel',             'HOSE', 'VN', 'VND'),
('DTL.VN', 'Dai Thien Loc',                   'Materials', 'Steel',             'HOSE', 'VN', 'VND'),
('PAN.VN', 'PAN Group',                       'Materials', 'Diversified',       'HOSE', 'VN', 'VND'),
('GMD.VN', 'Gemadept Corp',                   'Industrials', 'Logistics',       'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- IT & Telecom
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('FPT.VN', 'FPT Corporation',                 'Technology', 'IT Services',      'HOSE', 'VN', 'VND'),
('CMG.VN', 'CMC Group',                       'Technology', 'IT Services',      'HOSE', 'VN', 'VND'),
('VGI.VN', 'Viettel Global',                  'Technology', 'Telecom',          'HOSE', 'VN', 'VND'),
('FOX.VN', 'FPT Telecom',                     'Technology', 'Telecom',          'HOSE', 'VN', 'VND'),
('ELC.VN', 'Elcom Corp',                      'Technology', 'Electronics',      'HOSE', 'VN', 'VND'),
('ITD.VN', 'Intresco Corp',                   'Technology', 'IT Services',      'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Energy & Oil
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('GAS.VN', 'PetroVietnam Gas',                'Energy', 'Oil & Gas',          'HOSE', 'VN', 'VND'),
('PLX.VN', 'Petrolimex',                      'Energy', 'Oil Trading',        'HOSE', 'VN', 'VND'),
('BSR.VN', 'Binh Son Refinery',               'Energy', 'Refining',           'HOSE', 'VN', 'VND'),
('PVD.VN', 'PetroVietnam Drilling',           'Energy', 'Oilfield Services',  'HOSE', 'VN', 'VND'),
('PVS.VN', 'PetroVietnam Services',           'Energy', 'Oilfield Services',  'HNX',  'VN', 'VND'),
('POW.VN', 'PetroVietnam Power',              'Energy', 'Power Generation',   'HOSE', 'VN', 'VND'),
('PPC.VN', 'Pha Lai Power',                   'Energy', 'Power Generation',   'HOSE', 'VN', 'VND'),
('NT2.VN', 'Nhon Trach 2 Power',             'Energy', 'Power Generation',   'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Retail
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('MWG.VN', 'Mobile World Investment',         'Consumer Cyclical', 'Retail',          'HOSE', 'VN', 'VND'),
('PNJ.VN', 'Phu Nhuan Jewelry',              'Consumer Cyclical', 'Luxury Retail',   'HOSE', 'VN', 'VND'),
('DGW.VN', 'Digiworld Corp',                 'Consumer Cyclical', 'Distribution',    'HOSE', 'VN', 'VND'),
('FRT.VN', 'FPT Retail',                     'Consumer Cyclical', 'Retail',          'HOSE', 'VN', 'VND'),
('PHR.VN', 'Phuoc Hoa Rubber',               'Consumer Cyclical', 'Rubber',          'HOSE', 'VN', 'VND'),
('HAX.VN', 'Hang Xanh Motors',               'Consumer Cyclical', 'Auto Dealers',    'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Aviation & Transport
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('VJC.VN', 'Vietjet Air',                     'Industrials', 'Aviation',        'HOSE', 'VN', 'VND'),
('HVN.VN', 'Vietnam Airlines',                'Industrials', 'Aviation',        'HOSE', 'VN', 'VND'),
('ACV.VN', 'Airports Corp of Vietnam',        'Industrials', 'Airports',        'HOSE', 'VN', 'VND'),
('SCS.VN', 'Saigon Cargo Service',            'Industrials', 'Logistics',       'HOSE', 'VN', 'VND'),
('SGN.VN', 'Saigon Ground Services',          'Industrials', 'Ground Services', 'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Insurance & Securities
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('BVH.VN', 'Bao Viet Holdings',               'Financial Services', 'Insurance',       'HOSE', 'VN', 'VND'),
('BMI.VN', 'Bao Minh Insurance',              'Financial Services', 'Insurance',       'HOSE', 'VN', 'VND'),
('SSI.VN', 'SSI Securities',                  'Financial Services', 'Securities',      'HOSE', 'VN', 'VND'),
('VCI.VN', 'Viet Capital Securities',         'Financial Services', 'Securities',      'HOSE', 'VN', 'VND'),
('HCM.VN', 'HCMC Securities',                 'Financial Services', 'Securities',      'HOSE', 'VN', 'VND'),
('VND.VN', 'VNDirect Securities',             'Financial Services', 'Securities',      'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Construction & Industrial
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('CTD.VN', 'Coteccons',                        'Industrials', 'Construction',    'HOSE', 'VN', 'VND'),
('HBC.VN', 'Hoa Binh Construction',           'Industrials', 'Construction',    'HOSE', 'VN', 'VND'),
('VCG.VN', 'Vinaconex',                       'Industrials', 'Construction',    'HOSE', 'VN', 'VND'),
('REE.VN', 'REE Corp',                        'Industrials', 'Diversified',     'HOSE', 'VN', 'VND'),
('PC1.VN', 'Power Construction No.1',         'Industrials', 'Construction',    'HOSE', 'VN', 'VND'),
('GEX.VN', 'Gelex Group',                     'Industrials', 'Diversified',     'HOSE', 'VN', 'VND'),
('CII.VN', 'HCMC Infrastructure',             'Industrials', 'Infrastructure',  'HOSE', 'VN', 'VND'),
('FCN.VN', 'FECON Corp',                      'Industrials', 'Construction',    'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Chemicals & Rubber
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('DPM.VN', 'Petrovietnam Fertilizer',         'Materials', 'Chemicals',        'HOSE', 'VN', 'VND'),
('DCM.VN', 'Ca Mau Fertilizer',               'Materials', 'Chemicals',        'HOSE', 'VN', 'VND'),
('DGC.VN', 'Duc Giang Chemicals',             'Materials', 'Chemicals',        'HOSE', 'VN', 'VND'),
('CSV.VN', 'Cat Lai Port',                    'Materials', 'Chemicals',        'HOSE', 'VN', 'VND'),
('GVR.VN', 'Vietnam Rubber Group',            'Materials', 'Rubber',           'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Fisheries & Agriculture
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('VHC.VN', 'Vinh Hoan Corp',                  'Consumer Defensive', 'Seafood',        'HOSE', 'VN', 'VND'),
('IDI.VN', 'IDI International',               'Consumer Defensive', 'Seafood',        'HOSE', 'VN', 'VND'),
('ASM.VN', 'Sao Mai Group',                   'Consumer Defensive', 'Seafood',        'HOSE', 'VN', 'VND'),
('HAG.VN', 'Hoang Anh Gia Lai',              'Consumer Defensive', 'Agriculture',    'HOSE', 'VN', 'VND'),
('HNG.VN', 'HAGL Agrico',                     'Consumer Defensive', 'Agriculture',    'HOSE', 'VN', 'VND'),
('DBC.VN', 'Dabaco Group',                    'Consumer Defensive', 'Agriculture',    'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;

-- Others (Industrial Parks, Utilities, Diversified)
INSERT INTO stocks (symbol, name, sector, industry, exchange, country, currency) VALUES
('VEA.VN', 'VEAM Corp',                       'Industrials', 'Auto Parts',       'HOSE', 'VN', 'VND'),
('BWE.VN', 'Ba Ria Water',                    'Utilities',   'Water Utility',    'HOSE', 'VN', 'VND'),
('TNH.VN', 'Thanh Nien Holding',              'Healthcare',  'Pharmaceuticals',  'HOSE', 'VN', 'VND'),
('SZC.VN', 'Sonadezi Chau Duc',              'Real Estate', 'Industrial Parks', 'HOSE', 'VN', 'VND'),
('KBC.VN', 'Kinh Bac Urban',                 'Real Estate', 'Industrial Parks', 'HOSE', 'VN', 'VND'),
('ITA.VN', 'Tan Tao Investment',              'Real Estate', 'Industrial Parks', 'HOSE', 'VN', 'VND')
ON CONFLICT (symbol) DO NOTHING;
