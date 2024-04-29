from app.exchange_rates.schemes import ExchangeRequest, ExchangeResponse


class ExchangeRatesService:
    @staticmethod
    async def find_exchange_rate(request_data: ExchangeRequest) -> ExchangeResponse:
        exchange_rate = ExchangeResponse.model_validate(
            {
                "currency_from": "USDT",
                "currency_to": "TRX",
                "exchange": "binance",
                "rate": "8.21",
                "result": "821",
                "updated_at": 1714304596,
            }
        )
        return exchange_rate
