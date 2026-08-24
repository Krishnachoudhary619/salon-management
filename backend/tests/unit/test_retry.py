import pytest

from app.core.retry import retry_async


async def test_retry_returns_on_first_success() -> None:
    async def ok() -> str:
        return "ready"

    assert await retry_async(ok, attempts=3, base_delay=0.01, max_delay=0.01) == "ready"


async def test_retry_recovers_after_transient_failure() -> None:
    attempts = {"count": 0}
    slept: list[float] = []

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ConnectionError("db down")
        return "up"

    async def fake_sleep(delay: float) -> None:
        slept.append(delay)

    result = await retry_async(
        flaky,
        attempts=5,
        base_delay=0.1,
        max_delay=1.0,
        retry_on=(ConnectionError,),
        operation_name="database_connect",
        sleep=fake_sleep,
    )
    assert result == "up"
    assert attempts["count"] == 3
    assert len(slept) == 2
    assert slept[0] > 0


async def test_retry_raises_after_exhausting_attempts() -> None:
    async def always_fail() -> None:
        raise TimeoutError("nope")

    async def no_sleep(_: float) -> None:
        return None

    with pytest.raises(TimeoutError, match="nope"):
        await retry_async(
            always_fail,
            attempts=3,
            base_delay=0.01,
            max_delay=0.01,
            retry_on=(TimeoutError,),
            sleep=no_sleep,
        )


async def test_retry_rejects_invalid_attempts() -> None:
    async def ok() -> int:
        return 1

    with pytest.raises(ValueError, match="at least 1"):
        await retry_async(ok, attempts=0, base_delay=0.01, max_delay=0.01)
