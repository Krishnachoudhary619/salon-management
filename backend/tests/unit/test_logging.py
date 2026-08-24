from app.core.logging import _redact_sensitive_data


def test_sensitive_values_are_redacted() -> None:
    event = _redact_sensitive_data(
        None,
        "info",
        {
            "event": "login",
            "password": "super-secret",
            "access_token": "jwt-value",
            "email": "admin@salon.test",
            "payload": {"refresh_token": "abc", "name": "Admin"},
        },
    )
    assert event["password"] == "***REDACTED***"
    assert event["access_token"] == "***REDACTED***"
    assert event["email"] == "admin@salon.test"
    assert event["payload"]["refresh_token"] == "***REDACTED***"
    assert event["payload"]["name"] == "Admin"
