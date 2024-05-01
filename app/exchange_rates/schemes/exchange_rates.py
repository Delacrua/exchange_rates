from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict

__all__ = [
    "ExchangeRequest",
    "ExchangeResponse",
    "BinanceExchangeRequestResult",
    "KuCoinExchangeRequestResult",
]


class ExchangeEnum(str, Enum):
    Binance = "binance"
    KuCoin = "kucoin"


class ExchangeRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    currency_from: str
    currency_to: str
    exchange: ExchangeEnum | None | str
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
