from aiohttp import web
from aiohttp_pydantic import PydanticView
from aiohttp_pydantic.oas.typing import r200

from app.exchange_rates.schemes import ExchangeRequest, ExchangeResponse
from app.exchange_rates.services.exchange_rates import ExchangeRatesService


class ExchangeRatesView(PydanticView):
    async def get(self, request: ExchangeRequest) -> r200[ExchangeResponse]:
        response_data = await ExchangeRatesService.find_exchange_rate(
            request_data=request
        )
        return web.json_response(response_data.model_dump())
