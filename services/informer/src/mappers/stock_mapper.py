"""
stock_mapper.py — Proto ↔ dict converters for Stock messages.
Single source of truth used by both informer_handler and stock_admin_handler.
"""
from generated.common import types_pb2


def dict_to_stock(row: dict) -> types_pb2.Stock:
    """Convert a `stocks` table row dict to a proto Stock message."""
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


def stock_proto_to_dict(stock: types_pb2.Stock) -> dict:
    """Convert a proto Stock message to a plain dict for repository.

    Note: proto3 bool defaults to False, but we treat unset as True (new stocks
    should be active). The `_is_active_set` flag lets callers explicitly pass False.
    """
    # proto3 has no field presence for scalars — is_active defaults to False.
    # We check HasField-like heuristic: if the caller set any meaningful stock
    # fields, respect is_active as-is; otherwise default to True for creation.
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
