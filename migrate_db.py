#!/usr/bin/env python3
"""
Database migration entrypoint.

This script now uses Flask-Migrate/Alembic instead of ad-hoc ALTER TABLE logic.
Usage:
  python migrate_db.py
"""

from backend.app import create_app
from backend.database import upgrade_database


def migrate_database():
    app = create_app()
    with app.app_context():
        print("🔄 Applying database migrations (flask db upgrade)...")
        upgrade_database()
        print("✅ Database schema is up to date")


if __name__ == "__main__":
    migrate_database()
