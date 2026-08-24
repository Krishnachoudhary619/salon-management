from app.common.enums import SortOrder
from app.common.pagination import PaginatedData, PaginationParams
from app.common.responses import APIResponse, error_response, success_response


def test_pagination_defaults_and_offset() -> None:
    params = PaginationParams()
    assert params.page == 1
    assert params.limit == 20
    assert params.offset == 0
    assert params.sort_order == SortOrder.DESC


def test_pagination_offset_for_later_pages() -> None:
    params = PaginationParams(page=3, limit=10)
    assert params.offset == 20


def test_search_is_trimmed() -> None:
    params = PaginationParams(search="  color  ")
    assert params.search == "color"


def test_paginated_data_shape() -> None:
    page = PaginatedData(items=["a"], total=1, page=1, limit=20)
    assert page.model_dump() == {"items": ["a"], "total": 1, "page": 1, "limit": 20}


def test_success_and_error_wrappers() -> None:
    ok = success_response({"id": 1}, message="Created")
    assert ok.model_dump() == {
        "success": True,
        "message": "Created",
        "data": {"id": 1},
    }
    err = error_response("Validation error", [{"field": "email", "message": "required"}])
    assert err.success is False
    assert err.message == "Validation error"
    assert err.errors[0].field == "email"


def test_api_response_generic_contract() -> None:
    response = APIResponse[dict[str, str]](data={"status": "ok"})
    payload = response.model_dump()
    assert payload["success"] is True
    assert payload["message"] == "Operation successful"
    assert payload["data"] == {"status": "ok"}
