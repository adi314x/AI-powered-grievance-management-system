#!/usr/bin/env python3
"""Legacy shim: add-on tables are managed through normal Alembic revisions."""

from backend.app import create_app
from backend.database import upgrade_database


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("🔄 Applying migrations for add-on tables...")
        upgrade_database()
        print("✅ Done")
