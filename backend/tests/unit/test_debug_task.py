from app.workers.tasks.debug import debug_ping


def test_debug_ping_returns_ok() -> None:
    result = debug_ping.apply().get()

    assert result["status"] == "ok"
    assert "timestamp" in result
