from typing import Any


class AppException(Exception):
    """Base application exception mapped to a standardized API error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=404, errors=errors)


class ValidationException(AppException):
    def __init__(
        self,
        message: str = "Validation error",
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=422, errors=errors)


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Authentication required",
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=401, errors=errors)


class PermissionDeniedException(AppException):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=403, errors=errors)


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Resource conflict",
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=409, errors=errors)


class RateLimitException(AppException):
    def __init__(
        self,
        message: str = "Too many requests",
        *,
        retry_after: int = 60,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=429, errors=errors)
        self.retry_after = retry_after


class ServiceUnavailableException(AppException):
    def __init__(
        self,
        message: str = "Service unavailable",
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=503, errors=errors)
