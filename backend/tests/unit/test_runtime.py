from app.core.runtime import RuntimeState


async def test_runtime_tracks_inflight_and_drains() -> None:
    runtime = RuntimeState()
    runtime.mark_ready()
    assert runtime.ready is True
    assert await runtime.begin_request() is True
    assert runtime.inflight == 1
    await runtime.end_request()
    assert runtime.inflight == 0


async def test_runtime_rejects_requests_after_shutdown_starts() -> None:
    runtime = RuntimeState()
    runtime.mark_ready()
    assert await runtime.begin_request() is True
    await runtime.begin_shutdown(0.05)
    assert runtime.ready is False
    assert runtime.shutting_down is True
    assert runtime.inflight == 1
    assert await runtime.begin_request() is False
    await runtime.end_request()
    await runtime.begin_shutdown(0.05)
    assert runtime.inflight == 0
