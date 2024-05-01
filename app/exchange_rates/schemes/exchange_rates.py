from pydantic import BaseModel

__all__ = [
    "ExchangeRequest",
    "ExchangeResponse",
    "ExchangeRequestResult",
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


class ExchangeRequestResult(BaseModel):
    price: float | None = None
    symbol: str | None = None
    code: int | None = None
    msg: str | None = None
