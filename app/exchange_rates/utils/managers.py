from abc import ABC, abstractmethod
from decimal import Decimal

import aiohttp

from app.exchange_rates.schemes import ExchangeRequestResult
from app.exchange_rates.utils.exceptions import ExchangeRequestException  # type: ignore

__all__ = [
    "AbstractManager",
    "BinanceManager",
    "KuCoinManager",
]


class AbstractManager(ABC):

    @abstractmethod
    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        raise NotImplementedError


class BinanceManager(AbstractManager):
    GET_EXCHANGE_RATE_URL = f"https://api.binance.com/api/v3/ticker/price?symbol=%s"
    BINANCE_INVALID_SYMBOL_CODE = -1121

    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        symbol = currency_from + currency_to
        result = ExchangeRequestResult.model_validate(
            await self._get_symbol_exchange_rate(symbol)
        )
        if result.symbol is None and result.code == self.BINANCE_INVALID_SYMBOL_CODE:
            symbol = currency_to + currency_from
            result = ExchangeRequestResult.model_validate(
                await self._get_symbol_exchange_rate(symbol)
            )
            if result.price is not None:
                result.price = 1 / result.price

        if result.price is not None:
            return Decimal(result.price).quantize(Decimal("1.0000"))
        raise ExchangeRequestException(
            f"Exchange rate for conversion pair {currency_from} -> {currency_to} not found"
        )

    async def _get_symbol_exchange_rate(self, symbol: str, *args, **kwargs) -> dict:
        url = self.GET_EXCHANGE_RATE_URL % symbol.upper()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                result = await resp.json()
        return result


class KuCoinManager(AbstractManager):

    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        raise NotImplementedError
