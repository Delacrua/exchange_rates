import json
import time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exchange_rates.schemes import ExchangeRateRequest, ExchangeRateResponse
from app.exchange_rates.services import ExchangeRatesService, exchange_rates
from app.exchange_rates.services.exchange_rates import redis_client
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
                    "updated_at": 1683027600,
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
        monkeypatch.setattr(service, "_set_redis_cache_data", MagicMock(return_value=None))
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
        monkeypatch.setattr(service, "_set_redis_cache_data", MagicMock(return_value=None))
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

    async def test_fetch_pair_conversion_rate_with_intermediary_currency(self, monkeypatch):
        """
        Test the _fetch_pair_conversion_rate_with_intermediary_currency method works correctly.
        """
        service = ExchangeRatesService()
        monkeypatch.setattr(service, "_get_redis_cached_data", MagicMock(return_value=None))

        mock_coroutine = AsyncMock()
        mock_coroutine.get_exchange_rate.return_value = Decimal("8.4400")

        with patch.dict(service.MANAGERS, {"binance": lambda: mock_coroutine}):
            request_data = REQUEST_DATA

            rate, exchange = await service._fetch_pair_conversion_rate_with_intermediary_currency(request_data)  # act

            assert rate == Decimal("8.4400") * Decimal("8.4400")
            assert exchange == "binance"

    async def test_get_redis_cached_data(self, monkeypatch):
        """
        Test the _get_redis_cached_data method.
        """
        service = ExchangeRatesService()
        monkeypatch.setattr(
            service,
            "_get_redis_exchange_data_by_key",
            AsyncMock(return_value={"rate": "8.4400"}),
        )
        response = await service._get_redis_cached_data(REQUEST_DATA)
        assert response == {"rate": "8.4400"}

    async def test_get_redis_exchange_data_by_key(self, monkeypatch):
        """
        Test the _get_redis_exchange_data_by_key method.
        """
        service = ExchangeRatesService()
        expected_key = "USDTTRX-binance"
        expected_response = {
            "currency_from": "USDT",
            "currency_to": "TRX",
            "exchange": "binance",
            "rate": "8.4400",
            "result": "84400",
            "updated_at": int(time.time()),
        }
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = json.dumps(expected_response)
        monkeypatch.setattr(redis_client, "get", mock_redis_client.get)

        response = service._get_redis_exchange_data_by_key(
            currency_from="USDT",
            currency_to="TRX",
            exchange="binance",
            cache_max_seconds=60,
        )  # act

        assert response == expected_response
        mock_redis_client.get.assert_called_once_with(expected_key)
