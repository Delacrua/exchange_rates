import pytest
from aiohttp import web
from aiohttp_pydantic import oas

from app.exchange_rates.routes import setup_routes


@pytest.fixture
async def healthcheck_test_client(loop, aiohttp_client):
    app = web.Application()
    oas.setup(app, url_prefix="/docs")
    return await aiohttp_client(app)


@pytest.fixture
async def exchange_rate_test_client(loop, aiohttp_client):
    app = web.Application()
    setup_routes(app)
    return await aiohttp_client(app)
