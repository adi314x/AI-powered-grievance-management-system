import importlib
import os
import sys
from sqlalchemy import inspect
from backend.extensions import db

def _reload_config():
    import backend.config as config_module
    importlib.reload(config_module)
    config_module.Config.reload_from_env()
    return config_module

def _reload_app():
    # Order matters for SQLAlchemy extension reloads
    import backend.extensions as extensions_module
    importlib.reload(extensions_module)
    
    import backend.models as models_module
    importlib.reload(models_module)
    
    import backend.models_addons as addons_module
    importlib.reload(addons_module)
    
    import backend.app as app_module
    return importlib.reload(app_module)

def test_database_url_normalizes_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost:5432/grievance")
    config_module = _reload_config()
    assert config_module.Config.SQLALCHEMY_DATABASE_URI.startswith("postgresql://")

def test_create_app_does_not_create_tables_when_auto_create_disabled(monkeypatch, tmp_path):
    db_path = tmp_path / "no_autocreate.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "false")
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    monkeypatch.setenv("ENABLE_STARTUP_MODEL_LOAD", "false")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "phase3-test-secret")

    _reload_config()
    app_module = _reload_app()
    app = app_module.create_app()

    with app.app_context():
        from backend.extensions import db
        tables = inspect(db.engine).get_table_names()
        assert "users" not in tables

def test_create_app_creates_tables_when_auto_create_enabled(monkeypatch, tmp_path):
    db_path = tmp_path / "autocreate.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "true")
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    monkeypatch.setenv("ENABLE_STARTUP_MODEL_LOAD", "false")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "phase3-test-secret")
    monkeypatch.setenv("DEMO_EMAIL_MODE", "false")

    _reload_config()
    app_module = _reload_app()
    app = app_module.create_app()

    with app.app_context():
        from backend.extensions import db
        # If models were reloaded correctly, they will be in metadata
        tables = inspect(db.engine).get_table_names()
        assert "users" in tables

def test_upgrade_database_stamps_legacy_schema_before_upgrade(monkeypatch):
    import backend.database as database_module
    calls = {"stamp": 0, "upgrade": 0}
    class DummyInspector:
        @staticmethod
        def get_table_names():
            return ["users", "grievances"]
    class DummyDB:
        engine = object()
    monkeypatch.setattr(database_module, "db", DummyDB())
    monkeypatch.setattr(database_module, "inspect", lambda _engine: DummyInspector())
    monkeypatch.setattr(
        database_module,
        "stamp",
        lambda revision="head": calls.__setitem__("stamp", calls["stamp"] + 1),
    )
    monkeypatch.setattr(
        database_module,
        "upgrade",
        lambda: calls.__setitem__("upgrade", calls["upgrade"] + 1),
    )
    database_module.upgrade_database()
    assert calls["stamp"] == 1
    assert calls["upgrade"] == 1
