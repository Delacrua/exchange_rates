from aiohttp import web
from aiohttp_pydantic import PydanticView
from aiohttp_pydantic.oas.typing import r200

from app.exchange_rates.schemes import ExchangeRequest, ExchangeResponse
from app.exchange_rates.services.exchange_rates import ExchangeRatesService
from app.exchange_rates.utils.exceptions import ExchangeRatesServiceException


class ExchangeRatesView(PydanticView):
    async def get(self, request: ExchangeRequest) -> r200[ExchangeResponse]:
        try:
            response_data = await ExchangeRatesService().find_exchange_rate(
                request_data=request
            )
            return web.json_response(response_data.model_dump())
        except ExchangeRatesServiceException as exc:
            return web.json_response({"error": str(exc)}, status=400)
