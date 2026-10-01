from flask import Flask
import pytest

from backend.extensions import db
from backend import models  # noqa: F401 - ensure model metadata is registered
from backend import models_addons  # noqa: F401 - ensure add-on model metadata is registered
from backend.routes.auth import auth_bp
from backend.routes.grievances import grievances_bp
from backend.routes.admin import admin_bp
from backend.routes.addons import addons_bp
from backend.services.email_service import EmailService


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(grievances_bp, url_prefix="/api/grievances")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(addons_bp, url_prefix="/api")

    # Avoid network side effects in tests unless a case explicitly overrides.
    monkeypatch.setattr(EmailService, "send_email", staticmethod(lambda *args, **kwargs: True))
    monkeypatch.setattr(EmailService, "send_welcome_email", staticmethod(lambda *args, **kwargs: True))
    monkeypatch.setattr(EmailService, "send_password_reset_confirmation", staticmethod(lambda *args, **kwargs: True))
    monkeypatch.setattr(EmailService, "send_officer_assignment_notification", staticmethod(lambda *args, **kwargs: True))
    monkeypatch.setattr(EmailService, "send_status_update_notification", staticmethod(lambda *args, **kwargs: True))
    monkeypatch.setattr(EmailService, "send_grievance_notification", staticmethod(lambda *args, **kwargs: True))

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
