from typing import Any

from pydantic import BaseModel, Field


class ErrorItem(BaseModel):
    field: str | None = None
    message: str


class APIResponse[T](BaseModel):
    success: bool = True
    message: str = "Operation successful"
    data: T | None = None


class APIErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[ErrorItem] = Field(default_factory=list)


def success_response[T](
    data: T | None = None,
    message: str = "Operation successful",
) -> APIResponse[T]:
    return APIResponse(success=True, message=message, data=data)


def error_response(
    message: str,
    errors: list[dict[str, Any]] | list[ErrorItem] | None = None,
) -> APIErrorResponse:
    normalized: list[ErrorItem] = []
    for item in errors or []:
        if isinstance(item, ErrorItem):
            normalized.append(item)
        else:
            normalized.append(ErrorItem.model_validate(item))
    return APIErrorResponse(success=False, message=message, errors=normalized)
