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
    """
    Abstract base class for exchange rate managers.
    Attributes:
        GET_EXCHANGE_RATE_URL (str): The URL format for fetching exchange rates.
    """

    GET_EXCHANGE_RATE_URL: str

    @abstractmethod
    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        raise NotImplementedError

    async def _get_symbol_exchange_rate(self, symbol: str, *args, **kwargs) -> dict:
        """
        Fetch the exchange rate data for a given symbol from the exchange.
        Args:
            symbol (str): The currency pair symbol.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            dict: The exchange rate data
        Raises:
            exceptions.ExchangeRequestException: If unable to fetch exchange data.
        """
        url = self.GET_EXCHANGE_RATE_URL % symbol.upper()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                try:
                    result = await resp.json()
                except aiohttp.ClientError:
                    raise exceptions.ExchangeRequestException("Unable to fetch exchange data, exchange not responding")
        return result


class BinanceManager(AbstractManager):
    """
    Manager for fetching exchange rates from the Binance exchange.
    """

    GET_EXCHANGE_RATE_URL = f"https://api.binance.com/api/v3/ticker/price?symbol=%s"

    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        """
        Get the exchange rate between two currencies from the Binance exchange.
        Args:
            currency_from (str): The base currency code.
            currency_to (str): The target currency code.
        Returns:
            Decimal: The exchange rate from the base currency to the target currency.
        Raises:
            exceptions.PairNotFoundException: If the currency pair is not found on Binance.
        """

        price = None

        symbol = f"{currency_from}{currency_to}"
        response = schemes.BinanceRateRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
        if response.price is not None:
            price = response.price
        else:
            symbol = f"{currency_to}{currency_from}"
            response = schemes.BinanceRateRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
            if response.price is not None:
                price = 1 / response.price

        if price is not None:
            return price.quantize(Decimal("1.0000"))
        raise exceptions.PairNotFoundException(
            f"Exchange rate for conversion pair {currency_from} -> {currency_to} not found on Binance"
        )


class KuCoinManager(AbstractManager):
    """
    Manager for fetching exchange rates from the KuCoin exchange.
    """

    GET_EXCHANGE_RATE_URL = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=%s"

    async def get_exchange_rate(self, currency_from: str, currency_to: str) -> Decimal:
        """
        Get the exchange rate between two currencies from the KuCoin exchange
        Args:
            currency_from (str): The base currency code.
            currency_to (str): The target currency code
        Returns:
            Decimal: The exchange rate from the base currency to the target currency
        Raises:
            exceptions.PairNotFoundException: If the currency pair is not found on KuCoin.
        """

        price = None

        symbol = f"{currency_from}-{currency_to}"
        response = schemes.KuCoinRateRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
        if response.data is not None:
            price = response.data.price
        else:
            symbol = f"{currency_to}-{currency_from}"
            response = schemes.KuCoinRateRequestResult.model_validate(await self._get_symbol_exchange_rate(symbol))
            if response.data is not None:
                price = 1 / response.data.price

        if price is not None:
            return price.quantize(Decimal("1.0000"))
        raise exceptions.PairNotFoundException(
            f"Exchange rate for conversion pair {currency_from} -> {currency_to} not found on KuCoin"
        )
