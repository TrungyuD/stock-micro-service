-- =============================================================================
-- 01-schema.sql — Full database schema for Stock Trading Analysis Tool
-- Runs once on first container start via docker-entrypoint-initdb.d/
-- Order: this file runs BEFORE 02-seed.sql (alphabetical ordering)
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log initialization
DO $$
BEGIN
  RAISE NOTICE 'Stock DB initialized with TimescaleDB %', extversion
    FROM pg_extension WHERE extname = 'timescaledb';
END $$;

-- ============================================
-- STOCKS TABLE (relational metadata)
-- ============================================
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(50),
    country VARCHAR(50) DEFAULT 'US',
    currency VARCHAR(10) DEFAULT 'USD',
    market_cap BIGINT CHECK (market_cap IS NULL OR market_cap >= 0),
    description TEXT,
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stocks_symbol ON stocks (symbol);
CREATE INDEX idx_stocks_sector ON stocks (sector);
CREATE INDEX idx_stocks_exchange ON stocks (exchange);
CREATE INDEX idx_stocks_country ON stocks (country);

-- ============================================
-- OHLCV TABLE (time-series hypertable)
-- TimescaleDB hypertable — high write/query volume
-- ============================================
CREATE TABLE IF NOT EXISTS ohlcv (
    time TIMESTAMPTZ NOT NULL,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    open DECIMAL(12, 4) NOT NULL CHECK (open > 0),
    high DECIMAL(12, 4) NOT NULL CHECK (high > 0),
    low DECIMAL(12, 4) NOT NULL CHECK (low > 0),
    close DECIMAL(12, 4) NOT NULL CHECK (close > 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    adjusted_close DECIMAL(12, 4),
    UNIQUE (stock_id, time)
);

-- Convert to TimescaleDB hypertable (partition by time)
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

-- Composite index for stock + time range queries
CREATE INDEX idx_ohlcv_stock_time ON ohlcv (stock_id, time DESC);

-- Compression policy: compress chunks older than 30 days (~90% storage reduction)
ALTER TABLE ohlcv SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'stock_id'
);
SELECT add_compression_policy('ohlcv', INTERVAL '30 days', if_not_exists => TRUE);

-- Retention policy: drop data older than 10 years
SELECT add_retention_policy('ohlcv', INTERVAL '10 years', if_not_exists => TRUE);

-- ============================================
-- FINANCIAL REPORTS TABLE
-- Stores quarterly/annual income statement, balance sheet, cash flow
-- ============================================
CREATE TABLE IF NOT EXISTS financial_reports (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('Annual', 'Quarterly')),

    -- Income Statement
    revenue DECIMAL(18, 2),
    gross_profit DECIMAL(18, 2),
    operating_income DECIMAL(18, 2),
    net_income DECIMAL(18, 2),
    eps DECIMAL(10, 4),

    -- Balance Sheet
    total_assets DECIMAL(18, 2),
    total_liabilities DECIMAL(18, 2),
    shareholders_equity DECIMAL(18, 2),
    book_value_per_share DECIMAL(10, 4),

    -- Cash Flow
    operating_cash_flow DECIMAL(18, 2),
    free_cash_flow DECIMAL(18, 2),
    capex DECIMAL(18, 2),

    -- Key Metrics
    shares_outstanding BIGINT,
    debt_to_equity DECIMAL(10, 4),
    current_ratio DECIMAL(10, 4),
    roe DECIMAL(10, 4),
    roa DECIMAL(10, 4),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_id, report_date, report_type)
);

CREATE INDEX idx_financial_reports_stock ON financial_reports (stock_id, report_date DESC);

-- ============================================
-- INDICATORS TABLE (cached technical indicator calculations)
-- Avoids recomputing expensive rolling-window calculations
-- ============================================
CREATE TABLE IF NOT EXISTS indicators (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    time TIMESTAMPTZ NOT NULL,

    -- RSI (14-period)
    rsi_14 DECIMAL(6, 2),

    -- Moving Averages
    sma_20 DECIMAL(12, 4),
    sma_50 DECIMAL(12, 4),
    sma_200 DECIMAL(12, 4),
    ema_20 DECIMAL(12, 4),
    ema_50 DECIMAL(12, 4),

    -- MACD (12/26/9)
    macd_line DECIMAL(12, 4),
    macd_signal DECIMAL(12, 4),
    macd_histogram DECIMAL(12, 4),

    -- Bollinger Bands (20-period, 2 std dev)
    bb_upper DECIMAL(12, 4),
    bb_middle DECIMAL(12, 4),
    bb_lower DECIMAL(12, 4),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_id, time)
);

CREATE INDEX idx_indicators_stock_time ON indicators (stock_id, time DESC);

-- ============================================
-- VALUATION METRICS TABLE
-- Cached fundamental valuation ratios per stock
-- ============================================
CREATE TABLE IF NOT EXISTS valuation_metrics (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    trailing_pe DECIMAL(10, 4),
    forward_pe DECIMAL(10, 4),
    price_to_book DECIMAL(10, 4),
    peg_ratio DECIMAL(10, 4),
    price_to_sales DECIMAL(10, 4),
    ev_to_ebitda DECIMAL(10, 4),
    dividend_yield DECIMAL(8, 4),
    payout_ratio DECIMAL(8, 4),

    -- Valuation signal: 'Undervalued', 'Fair Value', 'Overvalued'
    valuation_signal VARCHAR(20),
    valuation_score DECIMAL(5, 2),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_id, calculated_at)
);

CREATE INDEX idx_valuation_stock ON valuation_metrics (stock_id, calculated_at DESC);

-- ============================================
-- WATCHLISTS (user -> named list of stocks)
-- ============================================
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, name)
);

-- ============================================
-- WATCHLIST ITEMS (many-to-many: watchlist <-> stocks)
-- ============================================
CREATE TABLE IF NOT EXISTS watchlist_items (
    id SERIAL PRIMARY KEY,
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (watchlist_id, stock_id)
);

CREATE INDEX idx_watchlist_items_watchlist ON watchlist_items (watchlist_id);

-- ============================================
-- USERS TABLE (authentication)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);

-- ============================================
-- REFRESH TOKENS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens (token_hash);
