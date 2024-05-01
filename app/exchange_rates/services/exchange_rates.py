import json
import time
from decimal import Decimal
from typing import TypeVar

import redis

from app.exchange_rates.schemes import ExchangeRequest, ExchangeResponse
from app.exchange_rates.utils import exceptions  # type: ignore
from app.exchange_rates.utils import managers
from app.settings import settings

Manager = TypeVar("Manager", bound=managers.AbstractManager)

redis_client = redis.Redis(host=settings.REDIS_HOST, db=0)


class ExchangeRatesService:
    MANAGERS = {
        "binance": managers.BinanceManager,
        "kucoin": managers.KuCoinManager,
    }

    async def find_exchange_rate(self, request_data: ExchangeRequest) -> ExchangeResponse:
        if request_data.cache_max_seconds:
            response = self._get_redis_cached_data(request_data)
            if response:
                return ExchangeResponse.model_validate(response)

        rate, exchange = await self._fetch_pair_conversion_rate(request_data)

        if rate is None:
            raise exceptions.ExchangeRatesServiceException(
                "Could not find exchange rate for currency pair on any of the supported exchanges. "
                "Currency pair is incorrect or not supported."
            )
        response_dict = self._form_response_dict(
            exchange=exchange, rate=rate, amount=request_data.amount  # type: ignore[arg-type]
        )

        redis_client.set(
            f"{request_data.currency_from}{request_data.currency_to}-{exchange}",
            json.dumps(response_dict),
        )
        return ExchangeResponse.model_validate(response_dict)

    async def _fetch_pair_conversion_rate(self, request_data: ExchangeRequest) -> tuple[Decimal | None, str | None]:
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
    def _form_response_dict(exchange: str, rate: Decimal, amount: int) -> dict:
        return {
            "currency_from": "USDT",
            "currency_to": "TRX",
            "exchange": f"{exchange}",
            "rate": f"{rate:.4f}",
            "result": f"{amount * rate:.2f}",
            "updated_at": int(time.time()),
        }

    def _get_redis_cached_data(self, request_data: ExchangeRequest) -> dict | None:
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
        if byte_data := redis_client.get(f"{currency_from}{currency_to}-{exchange}"):
            response = json.loads(byte_data)  # type: ignore[arg-type]
            if int(response.get("updated_at")) + cache_max_seconds > int(time.time()):
                return response
        return None
