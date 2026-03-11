"""
stock_mapper.py — Proto ↔ dict converters for v1 stock_pb2.Stock messages.
Used by v1 handlers (stock_handler.py, etc.). Contains no legacy proto imports.
For legacy types_pb2.Stock, see mappers/legacy_stock_mapper.py.
"""
from generated.informer.v1 import stock_pb2


def dict_to_stock(row: dict) -> stock_pb2.Stock:
    """Convert a `stocks` table row dict to a v1 proto Stock message."""
    return stock_pb2.Stock(
        id=row.get("id") or 0,
        symbol=row.get("symbol") or "",
        name=row.get("name") or "",
        sector=row.get("sector") or "",
        industry=row.get("industry") or "",
        exchange=row.get("exchange") or "",
        country=row.get("country") or "",
        currency=row.get("currency") or "",
        market_cap=row.get("market_cap") or 0,
        description=row.get("description") or "",
        website=row.get("website") or "",
        is_active=bool(row.get("is_active", True)),
    )


def stock_proto_to_dict(stock: stock_pb2.Stock) -> dict:
    """Convert a v1 stock_pb2.Stock proto message to a plain dict for repository."""
    return {
        "symbol": stock.symbol.strip().upper() if stock.symbol else "",
        "name": stock.name or "",
        "sector": stock.sector or None,
        "industry": stock.industry or None,
        "exchange": stock.exchange or None,
        "country": stock.country or "US",
        "currency": stock.currency or "USD",
        "market_cap": stock.market_cap if stock.market_cap else None,
        "description": stock.description or None,
        "website": stock.website or None,
        "is_active": bool(stock.is_active),
    }
