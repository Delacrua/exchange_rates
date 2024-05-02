import time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exchange_rates.schemes import ExchangeRateRequest, ExchangeRateResponse
from app.exchange_rates.services import ExchangeRatesService
from app.exchange_rates.utils import exceptions

# Test data
REQUEST_DATA = ExchangeRateRequest.model_validate(
    {
        "currency_from": "BTC",
        "currency_to": "USDT",
        "amount": 100,
        "exchange": None,
        "cache_max_seconds": 60,
    }
)


@pytest.mark.asyncio
class TestExchangeRatesService:
    async def test_find_exchange_rate_with_cached_data(self, monkeypatch):
        """
        Test the find_exchange_rate method when cached data is available in Redis.
        """
        service = ExchangeRatesService()
        monkeypatch.setattr(
            service,
            "_get_redis_cached_data",
            MagicMock(
                return_value={
                    "currency_from": "USDT",
                    "currency_to": "TRX",
                    "exchange": "binance",
                    "rate": "8.4400",
                    "result": "84400",
                    "updated_at": int(time.time()),
                }
            ),
        )

        response = await service.find_exchange_rate(REQUEST_DATA)  # act

        assert response.rate == "8.4400"

    async def test_find_exchange_rate_without_cached_data(self, monkeypatch):
        """
        Test the find_exchange_rate method when no cached data is available in Redis.
        """
        service = ExchangeRatesService()
        monkeypatch.setattr(service, "_get_redis_cached_data", MagicMock(return_value=None))
        monkeypatch.setattr(
            service, "_fetch_pair_conversion_rate", AsyncMock(return_value=(Decimal("8.4400"), "binance"))
        )

        response = await service.find_exchange_rate(REQUEST_DATA)  # act

        assert response.rate == "8.4400"

    async def test_find_exchange_rate_with_intermediary_currency(self, monkeypatch):
        """
        Test the find_exchange_rate method when an intermediary currency is required.
        """
        service = ExchangeRatesService()
        monkeypatch.setattr(service, "_get_redis_cached_data", MagicMock(return_value=None))
        monkeypatch.setattr(service, "_fetch_pair_conversion_rate", AsyncMock(return_value=(None, None)))
        monkeypatch.setattr(
            service,
            "_fetch_pair_conversion_rate_with_intermediary_currency",
            AsyncMock(return_value=(Decimal("8.4400"), "binance")),
        )

        response = await service.find_exchange_rate(REQUEST_DATA)  # act

        assert response.rate == "8.4400"

    async def test_find_exchange_rate_failure(self, monkeypatch):
        """
        Test the find_exchange_rate method when no exchange rate is found.
        """
        service = ExchangeRatesService()
        monkeypatch.setattr(service, "_get_redis_cached_data", MagicMock(return_value=None))
        monkeypatch.setattr(service, "_fetch_pair_conversion_rate", AsyncMock(return_value=(None, None)))
        monkeypatch.setattr(
            service,
            "_fetch_pair_conversion_rate_with_intermediary_currency",
            AsyncMock(return_value=(None, None)),
        )

        with pytest.raises(exceptions.ExchangeRatesServiceException):
            await service.find_exchange_rate(REQUEST_DATA)  # act

    async def test_fetch_pair_conversion_rate_success(self, monkeypatch):
        """
        Test the _fetch_pair_conversion_rate method works correctly.
        """
        service = ExchangeRatesService()
        monkeypatch.setattr(service, "_get_redis_cached_data", MagicMock(return_value=None))

        mock_coroutine = AsyncMock()
        mock_coroutine.get_exchange_rate.return_value = Decimal("8.4400")

        with patch.dict(service.MANAGERS, {"binance": lambda: mock_coroutine}):
            request_data = REQUEST_DATA

            rate, exchange = await service._fetch_pair_conversion_rate(request_data)  # act

            assert rate == Decimal("8.4400")
            assert exchange == "binance"
