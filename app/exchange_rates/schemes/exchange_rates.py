from pydantic import BaseModel

__all__ = [
    "ExchangeRequest",
    "ExchangeResponse",
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
