import pytest

import backend.app as app_module


def _set_base_env(monkeypatch, tmp_path):
    db_path = tmp_path / "phase9.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("ENABLE_STARTUP_MODEL_LOAD", "false")
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "false")


def test_health_endpoint_includes_runtime_checks(monkeypatch, tmp_path):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "phase9-health-secret")

    app = app_module.create_app()
    client = app.test_client()

    response = client.get("/health")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "healthy"
    assert payload["environment"] == "development"
    assert payload["database"]["connected"] is True
    assert payload["database"]["dialect"] == "sqlite"
    assert "model_loaded" in payload["ml"]
    assert "running" in payload["scheduler"]


def test_health_endpoint_returns_503_when_db_check_fails(monkeypatch, tmp_path):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "phase9-health-secret")

    app = app_module.create_app()
    client = app.test_client()

    def _raise_db_error(*_args, **_kwargs):
        raise RuntimeError("database unreachable")

    monkeypatch.setattr(app_module.db.session, "execute", _raise_db_error)

    response = client.get("/health")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["status"] == "degraded"
    assert payload["database"]["connected"] is False
    assert "database unreachable" in payload["database"]["error"]


def test_create_app_requires_secret_key_in_production(monkeypatch, tmp_path):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "dev-secret-key-change-in-production")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        app_module.create_app()


def test_production_requires_demo_email_mode_disabled(monkeypatch, tmp_path):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "phase9-prod-secret")
    monkeypatch.setenv("DEMO_EMAIL_MODE", "true")

    with pytest.raises(RuntimeError, match="DEMO_EMAIL_MODE"):
        app_module.create_app()


def test_demo_modes_default_to_false_when_unset(monkeypatch, tmp_path):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "phase9-dev-secret")
    monkeypatch.delenv("DEMO_EMAIL_MODE", raising=False)
    monkeypatch.delenv("DEMO_SMS_MODE", raising=False)

    app = app_module.create_app()

    assert app.config["DEMO_EMAIL_MODE"] is False
    assert app.config["DEMO_SMS_MODE"] is False
