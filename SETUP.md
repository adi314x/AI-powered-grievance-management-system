# Setup Guide

This guide is for running the full application (`backend/` + `frontend/`) locally.

## 1. Requirements

- Python 3.11+
- `pip`
- Git

Optional for production-like local testing:
- PostgreSQL

## 2. Clone and Install

```bash
git clone https://github.com/Santhakumarramesh/smart-grievance-system.git
cd smart-grievance-system

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

## 3. Configure Environment

Create `.env` from template:

```bash
cp env.template .env
```

Minimum local values:

```env
FLASK_ENV=development
SECRET_KEY=local-dev-secret
APP_BASE_URL=http://localhost:8000
DATABASE_URL=sqlite:///grievance.db
DEMO_EMAIL_MODE=false
DEMO_SMS_MODE=false
AUTO_CREATE_TABLES=false
ENABLE_STARTUP_MODEL_LOAD=true
ENABLE_SCHEDULER=true
SCHEDULER_AUTOSTART=false
```

## 4. Initialize Database

```bash
python -m flask --app backend.app:create_app db upgrade
python manage.py seed
```

Notes:
- `manage.py seed` applies migrations first, then seeds baseline admin/officer/citizen records for local testing.
- Use migration commands for schema changes; do not rely on `db.create_all()` in production.

## 5. Run the Application

```bash
python run.py
```

Open:
- App: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## 6. Seeded Local Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@grievance.gov` | `admin123` |
| Officer | `electricity@grievance.gov` | `officer123` |
| Citizen | `citizen@example.com` | `citizen123` |

## 7. Run Tests and Lint

```bash
ruff check backend tests
python -m pytest --cov=backend --cov-report=term-missing
```

## 8. Run Full Smoke Verification

Run the strict end-to-end smoke harness (isolated SQLite DB, migrations, seed, critical flow checks):

```bash
python scripts/smoke_test.py
```

This is useful before release/deploy and for proving core workflow health quickly.

## 9. Working with Migrations

Create migration after model updates:

```bash
python -m flask --app backend.app:create_app db migrate -m "describe change"
python -m flask --app backend.app:create_app db upgrade
```

## 10. Production Checklist (Minimum)

- Set `FLASK_ENV=production`
- Set a strong `SECRET_KEY`
- Set `APP_BASE_URL` to your public domain
- Use PostgreSQL `DATABASE_URL`
- Keep `AUTO_CREATE_TABLES=false`
- Keep `DEMO_EMAIL_MODE=false`
- Keep `DEMO_SMS_MODE=false`
- If running multiple instances, keep `SCHEDULER_AUTOSTART=false` on all but one

Use [DEPLOY.md](DEPLOY.md) for full deployment details.
