import json
import time
from decimal import Decimal
from typing import TypeVar

import redis

from app.exchange_rates.schemes import ExchangeRateRequest, ExchangeRateResponse
from app.exchange_rates.utils import exceptions  # type: ignore
from app.exchange_rates.utils import managers
from app.settings import settings

Manager = TypeVar("Manager", bound=managers.AbstractManager)

redis_client = redis.Redis(host=settings.REDIS_HOST, db=0)


class ExchangeRatesService:
    """
    A service class for handling exchange rate requests and fetching exchange rates.
    """

    MANAGERS = {
        "binance": managers.BinanceManager,
        "kucoin": managers.KuCoinManager,
    }

    async def find_exchange_rate(self, request_data: ExchangeRateRequest) -> ExchangeRateResponse:
        """
        Find the exchange rate for the given currency pair based on the request data.
        Args:
            request_data (ExchangeRateRequest): The request data containing the currency pair and other parameters.
        Returns:
            ExchangeRateResponse: The response object containing the exchange rate and conversion result.
        Raises:
            exceptions.ExchangeRatesServiceException: If the exchange rate for the currency pair cannot be found on
            any supported exchange.
        This method first checks if cached data is available in Redis and returns it if it's still valid.
        If no cached data is available, it attempts to fetch the exchange rate from the supported exchanges.
        If the direct conversion fails, it tries to fetch the exchange rate using an intermediary currency.
        If successful, it caches the result in Redis and returns the response object.
        """
        if request_data.cache_max_seconds:
            response = self._get_redis_cached_data(request_data)
            if response:
                return ExchangeRateResponse.model_validate(response)

        rate, exchange = await self._fetch_pair_conversion_rate(request_data)
        if rate is None:
            rate, exchange = await self._fetch_pair_conversion_rate_with_intermediary_currency(request_data)

        if rate is None:
            raise exceptions.ExchangeRatesServiceException(
                "Could not find exchange rate for currency pair on any of the supported exchanges. "
                "Currency pair is incorrect or not supported."
            )
        response_dict = self._form_response_dict(
            currency_from=request_data.currency_from,
            currency_to=request_data.currency_to,
            exchange=exchange,  # type: ignore[arg-type]
            rate=rate,
            amount=request_data.amount,  # type: ignore[arg-type]
        )

        redis_client.set(
            f"{request_data.currency_from}{request_data.currency_to}-{exchange}",
            json.dumps(response_dict),
        )
        return ExchangeRateResponse.model_validate(response_dict)

    async def _fetch_pair_conversion_rate(self, request_data: ExchangeRateRequest) -> tuple[Decimal | None, str | None]:
        """
        Fetch the exchange rate for the given currency pair from the requested exchange or supported exchanges
        Args:
            request_data (ExchangeRateRequest): The request data containing the currency pair and other parameters
        Returns:
            tuple[Decimal | None, str | None]: A tuple containing the exchange rate and the exchange name,
            or None if not found
        Raises:
            exceptions.ExchangeRatesServiceException: If unable to contact any of the supported exchanges
        This method attempts to fetch the exchange rate for the given currency pair from the requested exchange
        or iterates through the supported exchanges until a valid exchange rate is found.
        """

        rate = None
        if (exchange := request_data.exchange) is None:
            requests_failed = {k: False for k in self.MANAGERS}

            for key, manager_class in self.MANAGERS.items():
                try:
                    manager = manager_class()
                    rate = await manager.get_exchange_rate(request_data.currency_from, request_data.currency_to)
                    exchange = key
                    if rate:
                        break
                except exceptions.ExchangeRequestException as exc:
                    requests_failed[key] = True
                    continue
                except exceptions.ManagerException as exc:
                    continue
            if all(map(lambda x: x is True, requests_failed)):
                raise exceptions.ExchangeRatesServiceException(
                    "Unable to contact exchanges, all exchanges were not available during requests."
                )
        else:
            if manager_class := self.MANAGERS.get(exchange):  # type: ignore
                manager = manager_class()
                rate = await manager.get_exchange_rate(request_data.currency_from, request_data.currency_to)
            else:
                raise exceptions.ExchangeRatesServiceException(
                    "Invalid request parameter: exchange. The exchange is incorrect or not supported."
                )

        return rate, exchange

    @staticmethod
    async def _get_intermediary_currency(currency_from, currency_to) -> str:
        """
        Get the intermediary currency for converting between the given currency pair
        Args:
            currency_from (str): The base currency code.
            currency_to (str): The target currency code
        Returns:
            str: The intermediary currency code
        Note:
            This method is not implemented yet and currently returns a hardcoded value.
        """
        return "USDT"  # TO DO

    async def _fetch_pair_conversion_rate_with_intermediary_currency(
        self,
        request_data: ExchangeRateRequest,
    ) -> tuple[Decimal | None, str | None]:
        """
        Fetch the exchange rate for the given currency pair using an intermediary currency
        Args:
            request_data (ExchangeRateRequest): The request data containing the currency pair and other parameters
        Returns:
            tuple[Decimal | None, str | None]: A tuple containing the exchange rate and the exchange name,
            or None if not found
        This method fetches the exchange rates for converting the base currency to the intermediary currency
        and the intermediary currency to the target currency. It then calculates the overall exchange rate
        by multiplying the two rates.
        """

        intermediary_currency = await self._get_intermediary_currency(
            request_data.currency_from,
            request_data.currency_to,
        )
        rate = None
        if (exchange := request_data.exchange) is None:
            for key, manager_class in self.MANAGERS.items():
                try:
                    manager = manager_class()
                    rate_1 = await manager.get_exchange_rate(request_data.currency_from, intermediary_currency)
                    rate_2 = await manager.get_exchange_rate(intermediary_currency, request_data.currency_to)
                    rate = rate_1 * rate_2
                    exchange = key
                    if rate:
                        break
                except exceptions.ManagerException as exc:
                    continue

        else:
            if manager_class := self.MANAGERS.get(exchange):  # type: ignore
                manager = manager_class()
                rate_1 = await manager.get_exchange_rate(request_data.currency_from, intermediary_currency)
                rate_2 = await manager.get_exchange_rate(intermediary_currency, request_data.currency_to)
                rate = rate_1 * rate_2

        return rate, exchange

    @staticmethod
    def _form_response_dict(
        currency_from: str, currency_to: str, exchange: str, rate: Decimal, amount: Decimal
    ) -> dict:
        """
        Form the response dictionary with the exchange rate and conversion result
        Args:
            currency_from (str): The base currency code.
            currency_to (str): The target currency code.
            exchange (str): The name of the exchange.
            rate (Decimal): The exchange rate.
            amount (Decimal): The amount to be converted
        Returns:
            dict: A dictionary containing the exchange rate information and conversion result.
        """

        return {
            "currency_from": currency_from,
            "currency_to": currency_to,
            "exchange": f"{exchange}",
            "rate": f"{rate:.4f}",
            "result": f"{amount * rate:.2f}",
            "updated_at": int(time.time()),
        }

    def _get_redis_cached_data(self, request_data: ExchangeRateRequest) -> dict | None:
        """
        Get the cached exchange rate data from Redis based on the request data
        Args:
            request_data (ExchangeRateRequest): The request data containing the currency pair and other parameters
        Returns:
            dict | None: The cached exchange rate data if available, or None if not found
        This method checks if cached data is available in Redis for the given currency pair and exchange.
        If the exchange is specified in the request data, it checks for cached data for that exchange.
        If the exchange is not specified, it checks for cached data across all supported exchanges.
        """

        if request_data.exchange:
            data = self._get_redis_exchange_data_by_key(
                currency_from=request_data.currency_from,
                currency_to=request_data.currency_to,
                exchange=request_data.exchange,
                cache_max_seconds=request_data.cache_max_seconds,  # type: ignore[arg-type]
            )
            if data is not None:
                return data
        else:
            for exchange_key in self.MANAGERS:
                data = self._get_redis_exchange_data_by_key(
                    currency_from=request_data.currency_from,
                    currency_to=request_data.currency_to,
                    exchange=exchange_key,
                    cache_max_seconds=request_data.cache_max_seconds,  # type: ignore[arg-type]
                )
                if data is not None:
                    return data
        return None

    @staticmethod
    def _get_redis_exchange_data_by_key(
        currency_from: str,
        currency_to: str,
        exchange: str,
        cache_max_seconds: int,
    ) -> dict | None:
        """
        Get the cached exchange rate data from Redis for the given currency pair, exchange, and cache duration
        Args:
            currency_from (str): The base currency code.
            currency_to (str): The target currency code.
            exchange (str): The name of the exchange.
            cache_max_seconds (int): The maximum duration for which the cached data is considered valid
        Returns:
            dict | None: The cached exchange rate data if available and still valid, or None if not found or expired.
        """

        if byte_data := redis_client.get(f"{currency_from}{currency_to}-{exchange}"):
            response = json.loads(byte_data)  # type: ignore[arg-type]
            if int(response.get("updated_at")) + cache_max_seconds > int(time.time()):
                return response
        return None
