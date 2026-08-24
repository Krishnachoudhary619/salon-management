import asyncio

from app.core.logging import get_logger

logger = get_logger(__name__)


class RuntimeState:
    """Process-wide readiness and in-flight request tracking for graceful shutdown."""

    def __init__(self) -> None:
        self.ready = False
        self.shutting_down = False
        self._inflight = 0
        self._condition = asyncio.Condition()

    def mark_ready(self) -> None:
        self.ready = True
        self.shutting_down = False

    @property
    def inflight(self) -> int:
        return self._inflight

    async def begin_request(self) -> bool:
        """Reserve a slot. Returns False when the process is draining."""
        async with self._condition:
            if self.shutting_down:
                return False
            self._inflight += 1
            return True

    async def end_request(self) -> None:
        async with self._condition:
            self._inflight = max(0, self._inflight - 1)
            if self._inflight == 0:
                self._condition.notify_all()

    async def begin_shutdown(self, drain_seconds: float) -> None:
        self.ready = False
        self.shutting_down = True
        async with self._condition:
            try:
                async with asyncio.timeout(drain_seconds):
                    await self._wait_until_idle()
            except TimeoutError:
                logger.warning(
                    "graceful_shutdown_timeout",
                    inflight=self._inflight,
                    timeout_seconds=drain_seconds,
                )

    async def _wait_until_idle(self) -> None:
        while self._inflight > 0:
            await self._condition.wait()
