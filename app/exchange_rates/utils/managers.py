from abc import ABC, abstractmethod
from decimal import Decimal

import aiohttp

from app.exchange_rates import schemes
from app.exchange_rates.utils import exceptions  # type: ignore

__all__ = [
    "AbstractManager",
    "BinanceManager",
    "KuCoinManager",
]


class AbstractManager(ABC):
    GET_EXCHANGE_RATE_URL: str

    @abstractmethod
    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        raise NotImplementedError

    async def _get_symbol_exchange_rate(self, symbol: str, *args, **kwargs) -> dict:
        url = self.GET_EXCHANGE_RATE_URL % symbol.upper()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                try:
                    result = await resp.json()
                except aiohttp.ClientError:
                    raise exceptions.ExchangeRequestException("Unable to fetch exchange data, exchange not responding")
        return result


class BinanceManager(AbstractManager):
    GET_EXCHANGE_RATE_URL = f"https://api.binance.com/api/v3/ticker/price?symbol=%s"

    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        price = None

        symbol = f"{currency_from}{currency_to}"
        response = schemes.BinanceExchangeRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
        if response.price is not None:
            price = response.price
        else:
            symbol = f"{currency_to}{currency_from}"
            response = schemes.BinanceExchangeRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
            if response.price is not None:
                price = 1 / response.price

        if price is not None:
            return price.quantize(Decimal("1.0000"))
        raise exceptions.PairNotFoundException(
            f"Exchange rate for conversion pair {currency_from} -> {currency_to} not found on Binance"
        )


class KuCoinManager(AbstractManager):
    GET_EXCHANGE_RATE_URL = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=%s"

    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        price = None

        symbol = f"{currency_from}-{currency_to}"
        response = schemes.KuCoinExchangeRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
        if response.data is not None:
            price = response.data.price
        else:
            symbol = f"{currency_to}-{currency_from}"
            response = schemes.KuCoinExchangeRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
            if response.data is not None:
                price = 1 / response.data.price

        if price is not None:
            return price.quantize(Decimal("1.0000"))
        raise exceptions.PairNotFoundException(
            f"Exchange rate for conversion pair {currency_from} -> {currency_to} not found on KuCoin"
        )
