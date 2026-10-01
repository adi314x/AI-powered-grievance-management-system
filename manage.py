#!/usr/bin/env python3
"""Project management CLI (migrations + seeding)."""

from flask.cli import FlaskGroup

from backend.app import create_app
from backend.seed import seed_database


cli = FlaskGroup(create_app=create_app)


@cli.command("seed")
def seed_command():
    """Apply migrations and seed demo data."""
    seed_database(run_migrations=True)


if __name__ == "__main__":
    cli()
