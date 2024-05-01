from decimal import Decimal

from pydantic import BaseModel

__all__ = [
    "ExchangeRequest",
    "ExchangeResponse",
    "BinanceExchangeRequestResult",
    "KuCoinExchangeRequestResult",
]


class ExchangeRequest(BaseModel):
    currency_from: str
    currency_to: str
    exchange: str | None
    amount: int
    cache_max_seconds: int | None


class ExchangeResponse(BaseModel):
    currency_from: str
    currency_to: str
    exchange: str
    rate: str
    result: str
    updated_at: int


class BinanceExchangeRequestResult(BaseModel):
    price: Decimal | None = None
    symbol: str | None = None
    code: int | None = None
    msg: str | None = None


class Data(BaseModel):
    bestAsk: Decimal
    bestAskSize: Decimal
    bestBid: Decimal
    bestBidSize: Decimal
    price: Decimal
    sequence: str
    size: Decimal
    time: int


class KuCoinExchangeRequestResult(BaseModel):
    code: str | None
    data: Data | None
