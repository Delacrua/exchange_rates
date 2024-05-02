import pytest

pytestmark = pytest.mark.asyncio


async def test_healthcheck(healthcheck_test_client):
    client = await healthcheck_test_client

    resp = await client.get("/docs")  # act

    assert resp.status == 200
