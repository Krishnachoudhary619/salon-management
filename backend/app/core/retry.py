import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Final

from app.core.logging import get_logger

logger = get_logger(__name__)

_JITTER_SPREAD: Final[float] = 0.5


async def retry_async[T](
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    base_delay: float,
    max_delay: float,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    operation_name: str = "operation",
    sleep: Callable[[float], Awaitable[None]] | None = None,
) -> T:
    """Retry an async operation with exponential backoff and equal jitter."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    wait = sleep or asyncio.sleep
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except retry_on as exc:
            last_error = exc
            if attempt >= attempts:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = delay * (_JITTER_SPREAD + random.random() * (1 - _JITTER_SPREAD))
            logger.warning(
                "retrying_operation",
                operation=operation_name,
                attempt=attempt,
                attempts=attempts,
                delay_seconds=round(delay, 3),
                error=str(exc),
            )
            await wait(delay)
    assert last_error is not None
    logger.error(
        "operation_failed",
        operation=operation_name,
        attempts=attempts,
        error=str(last_error),
    )
    raise last_error
