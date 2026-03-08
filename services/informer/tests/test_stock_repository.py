"""Tests for repositories/stock_repository.py — mocked DB operations."""
from unittest.mock import MagicMock

from repositories.stock_repository import StockRepository


class TestStockRepository:
    """StockRepository delegates SQL to the db_pool.execute method."""

    def test_get_by_symbol(self, mock_db_pool, sample_stock_metadata):
        mock_db_pool.execute.return_value = sample_stock_metadata
        repo = StockRepository(mock_db_pool)

        result = repo.get_by_symbol("AAPL")
        assert result["symbol"] == "AAPL"
        mock_db_pool.execute.assert_called_once()

    def test_get_by_symbol_not_found(self, mock_db_pool):
        mock_db_pool.execute.return_value = None
        repo = StockRepository(mock_db_pool)

        result = repo.get_by_symbol("ZZZZ")
        assert result is None

    def test_get_by_id(self, mock_db_pool, sample_stock_metadata):
        mock_db_pool.execute.return_value = sample_stock_metadata
        repo = StockRepository(mock_db_pool)

        result = repo.get_by_id(1)
        assert result["id"] == 1

    def test_get_all_active(self, mock_db_pool, sample_stock_metadata):
        mock_db_pool.execute.return_value = [sample_stock_metadata]
        repo = StockRepository(mock_db_pool)

        result = repo.get_all_active()
        assert len(result) == 1

    def test_search_with_query(self, mock_db_pool, sample_stock_metadata):
        # First call: count, second call: rows
        mock_db_pool.execute.side_effect = [
            {"cnt": 1},
            [sample_stock_metadata],
        ]
        repo = StockRepository(mock_db_pool)

        rows, total = repo.search(query="AAPL", page=1, page_size=20)
        assert total == 1
        assert len(rows) == 1

    def test_search_empty(self, mock_db_pool):
        mock_db_pool.execute.side_effect = [{"cnt": 0}, None]
        repo = StockRepository(mock_db_pool)

        rows, total = repo.search()
        assert total == 0
        assert rows == []

    def test_upsert(self, mock_db_pool, sample_stock_metadata):
        mock_db_pool.execute.return_value = {"id": 42}
        repo = StockRepository(mock_db_pool)

        stock_id = repo.upsert(sample_stock_metadata)
        assert stock_id == 42
