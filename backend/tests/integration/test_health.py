from httpx import AsyncClient

from app import __version__
from app.core.config import Settings
from app.core.constants import REQUEST_ID_HEADER, RETRY_AFTER_HEADER


async def test_liveness_probe(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == __version__
    assert REQUEST_ID_HEADER in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Cache-Control"] == "no-store"


async def test_readiness_probe_when_database_check_skipped(client: AsyncClient) -> None:
    response = await client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["checks"]["app"]["status"] == "ok"
    assert body["data"]["checks"]["database"]["status"] == "ok"


async def test_readiness_fails_while_draining(app, client: AsyncClient) -> None:
    app.state.runtime.shutting_down = True
    app.state.runtime.ready = False
    ready = await client.get("/ready")
    assert ready.status_code == 503
    assert ready.json()["success"] is False
    assert RETRY_AFTER_HEADER in ready.headers
    live = await client.get("/health")
    assert live.status_code == 200


async def test_invalid_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/health", headers={REQUEST_ID_HEADER: "not-a-uuid"})
    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] != "not-a-uuid"


async def test_rate_limit_returns_standard_envelope(app, client: AsyncClient) -> None:
    app.state.settings = Settings(
        APP_ENV="test",
        JWT_SECRET="unit-test-secret-key-must-be-32-chars",
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_REQUESTS=2,
        RATE_LIMIT_WINDOW_SECONDS=60,
        WAIT_FOR_DATABASE=False,
        READY_CHECK_DATABASE=False,
    )
    assert (await client.get("/openapi.json")).status_code == 200
    assert (await client.get("/openapi.json")).status_code == 200
    limited = await client.get("/openapi.json")
    assert limited.status_code == 429
    body = limited.json()
    assert body["success"] is False
    assert body["message"] == "Too many requests"
    assert limited.headers[RETRY_AFTER_HEADER]


async def test_unknown_host_is_rejected(app, client: AsyncClient) -> None:
    app.state.settings = Settings(
        APP_ENV="test",
        JWT_SECRET="unit-test-secret-key-must-be-32-chars",
        ALLOWED_HOSTS="api.salon.test",
        RATE_LIMIT_ENABLED=False,
        WAIT_FOR_DATABASE=False,
        READY_CHECK_DATABASE=False,
    )
    response = await client.get("/health")
    assert response.status_code == 400
    assert response.json()["success"] is False
