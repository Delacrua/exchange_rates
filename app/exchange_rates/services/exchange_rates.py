from decimal import Decimal
from typing import TypeVar

from app.exchange_rates.schemes import ExchangeRequest, ExchangeResponse
from app.exchange_rates.utils import exceptions  # type: ignore
from app.exchange_rates.utils import managers

Manager = TypeVar("Manager", bound=managers.AbstractManager)


class ExchangeRatesService:
    MANAGERS = {
        "binance": managers.BinanceManager,
        "kucoin": managers.KuCoinManager,
    }

    async def find_exchange_rate(
        self, request_data: ExchangeRequest
    ) -> ExchangeResponse:
        rate = None

        if (exchange := request_data.exchange) is None:
            for key, manager_class in self.MANAGERS.items():
                try:
                    manager = manager_class()
                    rate = await self._process_exchange_rate_request(
                        manager=manager,
                        currency_from=request_data.currency_from,
                        currency_to=request_data.currency_to,
                    )
                    exchange = key
                except exceptions.ExchangeRequestException as exc:
                    continue
                except NotImplementedError:
                    continue

        else:

            if manager_class := self.MANAGERS.get(exchange):  # type: ignore
                manager = manager_class()
                rate = await self._process_exchange_rate_request(
                    manager=manager,
                    currency_from=request_data.currency_from,
                    currency_to=request_data.currency_to,
                )
            else:
                raise exceptions.ExchangeRatesServiceException(
                    "Invalid request parameter: exchange. The exchange is incorrect or not supported"
                )

        if rate is None:
            raise exceptions.ExchangeRatesServiceException(
                "Could not find exchange rate for currency pair"
            )

        response = ExchangeResponse.model_validate(
            {
                "currency_from": "USDT",
                "currency_to": "TRX",
                "exchange": f"{exchange}",
                "rate": f"{rate:.4f}",
                "result": f"{request_data.amount * rate:.2f}",
                "updated_at": 1714304596,
            }
        )
        return response

    @staticmethod
    async def _process_exchange_rate_request(
        manager: Manager,
        currency_from: str,
        currency_to: str,
    ) -> Decimal:
        rate = await manager.get_exchange_rate(currency_from, currency_to)
        return rate
