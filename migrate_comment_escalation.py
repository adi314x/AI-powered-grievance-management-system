#!/usr/bin/env python3
"""
Legacy migration shim for comment escalation fields.

The schema is now managed by Flask-Migrate revisions.
Usage:
  python migrate_comment_escalation.py
"""

from backend.app import create_app
from backend.database import upgrade_database


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("🔄 Applying migrations (comment escalation fields are revision-managed)...")
        upgrade_database()
        print("✅ Done")
