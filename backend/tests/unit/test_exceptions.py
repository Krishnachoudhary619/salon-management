from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    RateLimitException,
    ServiceUnavailableException,
    UnauthorizedException,
    ValidationException,
)


def test_exception_status_codes() -> None:
    assert NotFoundException().status_code == 404
    assert ValidationException().status_code == 422
    assert UnauthorizedException().status_code == 401
    assert PermissionDeniedException().status_code == 403
    assert ConflictException().status_code == 409
    assert RateLimitException().status_code == 429
    assert RateLimitException(retry_after=15).retry_after == 15
    assert ServiceUnavailableException().status_code == 503


def test_exception_preserves_errors() -> None:
    exc = ValidationException(
        "Invalid payload",
        errors=[{"field": "price", "message": "Must be > 0"}],
    )
    assert exc.message == "Invalid payload"
    assert exc.errors[0]["field"] == "price"
