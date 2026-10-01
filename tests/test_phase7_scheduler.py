import pytest
from backend import app as app_module

def test_scheduler_autostart_disabled_by_default(monkeypatch):
    starts = {"count": 0}

    monkeypatch.setenv("ENABLE_SCHEDULER", "true")
    monkeypatch.setenv("SCHEDULER_AUTOSTART", "false")
    monkeypatch.setenv("ENABLE_STARTUP_MODEL_LOAD", "false")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("DEMO_EMAIL_MODE", "false")
    monkeypatch.setenv("SECRET_KEY", "phase7-test-secret")
    
    monkeypatch.setattr(app_module, "_is_flask_db_command", lambda: False)
    monkeypatch.setattr(
        app_module.scheduler,
        "start",
        lambda: starts.__setitem__("count", starts["count"] + 1),
    )

    app_module.create_app()
    assert starts["count"] == 0
