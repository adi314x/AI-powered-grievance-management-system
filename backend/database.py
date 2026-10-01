"""Database migration utilities."""

from flask_migrate import stamp, upgrade
from sqlalchemy import inspect

from backend.extensions import db


def upgrade_database():
    """
    Ensure schema is managed by Alembic and apply latest revisions.

    For legacy installs that already have app tables (from create_all) but no
    alembic version table, this stamps the current DB at head before upgrades.
    """
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    has_alembic_version = "alembic_version" in tables
    has_legacy_tables = bool({"users", "grievances", "otp_requests"} & tables)

    if has_legacy_tables and not has_alembic_version:
        print("⚠ Detected existing schema without Alembic version tracking; stamping current head")
        stamp(revision="head")

    upgrade()
