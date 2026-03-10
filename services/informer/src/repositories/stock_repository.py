"""
stock_repository.py — CRUD operations for the `stocks` table.
All queries are parameterized; no f-strings in SQL.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StockRepository:
    """Data-access layer for the `stocks` relational table."""

    def __init__(self, db_pool) -> None:
        self._db = db_pool

    # ─── reads ────────────────────────────────────────────────────────────────

    def get_by_symbol(self, symbol: str) -> Optional[dict]:
        """Return a single stock row by ticker symbol, or None."""
        return self._db.execute(
            """
            SELECT id, symbol, name, sector, industry, exchange,
                   country, currency, market_cap, description, website, is_active,
                   created_at, updated_at
              FROM stocks
             WHERE symbol = %s
            """,
            (symbol.upper(),),
            fetch="one",
        )

    def get_by_symbols(self, symbols: list[str]) -> list[dict]:
        """Return stock rows matching any of the given symbols (batch query)."""
        if not symbols:
            return []
        return self._db.execute(
            """
            SELECT id, symbol, name, sector, industry, exchange,
                   country, currency, market_cap, description, website, is_active,
                   created_at, updated_at
              FROM stocks
             WHERE symbol = ANY(%s)
            """,
            ([s.upper() for s in symbols],),
            fetch="all",
        ) or []

    def get_by_id(self, stock_id: int) -> Optional[dict]:
        """Return a single stock row by primary key, or None."""
        return self._db.execute(
            "SELECT * FROM stocks WHERE id = %s",
            (stock_id,),
            fetch="one",
        )

    def get_all_active(self) -> list[dict]:
        """Return all stocks where is_active = TRUE."""
        return self._db.execute(
            "SELECT * FROM stocks WHERE is_active = TRUE ORDER BY symbol",
            fetch="all",
        )

    def search(
        self,
        query: str = "",
        exchange: str = "",
        sector: str = "",
        country: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Full-text search across symbol/name with optional exchange/sector filters.

        Returns:
            (rows, total_count) tuple for pagination.
        """
        conditions = ["is_active = TRUE"]
        params: list = []

        if query:
            conditions.append("(symbol ILIKE %s OR name ILIKE %s)")
            like = f"%{query}%"
            params.extend([like, like])
        if exchange:
            conditions.append("exchange = %s")
            params.append(exchange)
        if sector:
            conditions.append("sector = %s")
            params.append(sector)
        if country:
            conditions.append("country = %s")
            params.append(country)

        where = " AND ".join(conditions)
        offset = (page - 1) * page_size

        # total count
        count_row = self._db.execute(
            f"SELECT COUNT(*) AS cnt FROM stocks WHERE {where}",
            tuple(params),
            fetch="one",
        )
        total = count_row["cnt"] if count_row else 0

        # paginated rows
        rows = self._db.execute(
            f"""
            SELECT id, symbol, name, sector, industry, exchange,
                   country, currency, market_cap, description, website, is_active
              FROM stocks
             WHERE {where}
             ORDER BY symbol
             LIMIT %s OFFSET %s
            """,
            tuple(params) + (page_size, offset),
            fetch="all",
        )
        return rows or [], total

    # ─── writes ───────────────────────────────────────────────────────────────

    def upsert(self, stock_data: dict) -> int:
        """
        Insert or update a stock row.

        Args:
            stock_data: dict with keys matching `stocks` columns.

        Returns:
            The stock id (int).
        """
        row = self._db.execute(
            """
            INSERT INTO stocks
                (symbol, name, sector, industry, exchange, country, currency,
                 market_cap, description, website, is_active, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (symbol) DO UPDATE SET
                name        = EXCLUDED.name,
                sector      = EXCLUDED.sector,
                industry    = EXCLUDED.industry,
                exchange    = EXCLUDED.exchange,
                country     = EXCLUDED.country,
                currency    = EXCLUDED.currency,
                market_cap  = EXCLUDED.market_cap,
                description = EXCLUDED.description,
                website     = EXCLUDED.website,
                is_active   = EXCLUDED.is_active,
                updated_at  = NOW()
            RETURNING id
            """,
            (
                stock_data.get("symbol", "").upper(),
                stock_data.get("name", ""),
                stock_data.get("sector"),
                stock_data.get("industry"),
                stock_data.get("exchange"),
                stock_data.get("country", "US"),
                stock_data.get("currency", "USD"),
                stock_data.get("market_cap"),
                stock_data.get("description"),
                stock_data.get("website"),
                stock_data.get("is_active", True),
            ),
            fetch="one",
        )
        stock_id = row["id"]
        logger.debug("Upserted stock %s → id=%s", stock_data.get("symbol"), stock_id)
        return stock_id

    def soft_delete(self, symbol: str) -> bool:
        """Set is_active=FALSE for a stock. Returns True if row existed."""
        row = self._db.execute(
            """
            UPDATE stocks SET is_active = FALSE, updated_at = NOW()
             WHERE symbol = %s
            RETURNING id
            """,
            (symbol.upper(),),
            fetch="one",
        )
        return row is not None
