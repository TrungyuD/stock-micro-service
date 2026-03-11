"""
legacy_stock_mapper.py — Proto ↔ dict converters for LEGACY types_pb2.Stock messages.
Used only by informer_handler.py and stock_admin_handler.py (legacy gRPC service).
Kept separate from stock_mapper.py to avoid loading v1 protos in the same process.
"""
from generated.common import types_pb2


def dict_to_legacy_stock(row: dict) -> types_pb2.Stock:
    """Convert a `stocks` table row dict to a legacy types_pb2.Stock proto message."""
    return types_pb2.Stock(
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


def stock_legacy_proto_to_dict(stock: types_pb2.Stock) -> dict:
    """Convert a legacy types_pb2.Stock proto message to a plain dict for repository."""
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
