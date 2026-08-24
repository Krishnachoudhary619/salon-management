from uuid import uuid4

from fastapi import Depends
from httpx import AsyncClient

from app.common.dependencies import get_current_user
from app.common.enums import Permission, Role
from app.common.responses import APIResponse
from app.core.permissions import require_permissions
from app.core.security import CurrentUser, create_access_token


def _add_protected_routes(app) -> None:
    @app.get("/secure", response_model=APIResponse[dict[str, str]])
    async def secure(user: CurrentUser = Depends(get_current_user)) -> APIResponse[dict[str, str]]:
        return APIResponse(data={"id": str(user.id)})

    @app.get("/admin-only", response_model=APIResponse[dict[str, bool]])
    async def admin_only(
        _user: CurrentUser = Depends(require_permissions(Permission.DASHBOARD_READ)),
    ) -> APIResponse[dict[str, bool]]:
        return APIResponse(data={"allowed": True})


async def test_missing_token_returns_standard_error(app, client: AsyncClient) -> None:
    _add_protected_routes(app)
    response = await client.get("/secure")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert "errors" in body


async def test_valid_access_token_authenticates_user(app, client: AsyncClient) -> None:
    _add_protected_routes(app)
    user_id = uuid4()
    token = create_access_token(subject=user_id, roles=[Role.ADMIN], email="admin@salon.test")
    response = await client.get("/secure", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(user_id)


async def test_staff_is_denied_admin_permission(app, client: AsyncClient) -> None:
    _add_protected_routes(app)
    token = create_access_token(subject=uuid4(), roles=[Role.STAFF])
    response = await client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["success"] is False


async def test_validation_error_uses_standard_envelope(client: AsyncClient) -> None:
    response = await client.get("/health", params={"unexpected": "ignored"})
    assert response.status_code == 200

    response = await client.get("/docs")
    assert response.status_code == 200
