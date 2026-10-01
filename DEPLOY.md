# Smart Grievance System Deployment Guide

This project supports two runtime profiles:

- Local development (`SQLite`, optional console email mode for debugging)
- Production deployment (`PostgreSQL`, real email provider mode)

Related docs:
- Local setup: [SETUP.md](SETUP.md)
- API map: [API_SUMMARY.md](API_SUMMARY.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)

## 1. Required Runtime Configuration

Set these variables in your hosting environment.

| Variable | Required | Example |
|---|---|---|
| `FLASK_ENV` | Yes | `production` |
| `SECRET_KEY` | Yes | random 32+ char string |
| `APP_BASE_URL` | Yes | `https://your-domain.com` |
| `DATABASE_URL` | Yes | `postgresql://user:pass@host:5432/db` |
| `DEMO_EMAIL_MODE` | Yes | `false` in production |
| `AUTO_CREATE_TABLES` | Yes | `false` |
| `ENABLE_SCHEDULER` | Yes | `true` |
| `SCHEDULER_AUTOSTART` | Yes | `false` (on web workers) |
| `FORMSPREE_ENDPOINT` | No | `https://formspree.io/f/...` |

If `DEMO_EMAIL_MODE=false`, configure at least one provider:

- **SMTP**: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- **Fallback**: `FORMSPREE_ENDPOINT`

## 2. Render Deployment (Blueprint Recommended)

This repo includes `render.yaml` with:

- Python web service
- health check path (`/health`)
- managed PostgreSQL service binding for `DATABASE_URL`
- production-safe defaults (`AUTO_CREATE_TABLES=false`, scheduler autostart off)

### Steps

1. Open Render Dashboard → **New** → **Blueprint**.
2. Connect this GitHub repository.
3. Fill missing `sync: false` values (for example `APP_BASE_URL`, SMTP credentials).
4. Deploy.

## 3. Render Deployment (Manual Service Setup)

Use these values:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn "backend.app:create_app()" --bind 0.0.0.0:$PORT`
- Runtime: Python 3.11
- Health check path: `/health`

Attach a PostgreSQL database and map its connection string to `DATABASE_URL`.

## 4. Migrations and Seed Data

Run after first deployment (Render shell or release command):

```bash
python -m flask --app backend.app:create_app db upgrade
python manage.py seed
```

`manage.py seed` runs migrations first, then loads baseline local accounts/data.

## 5. Scheduler and Background Jobs

The app includes background tasks for comment escalation and scheduled retraining.

- Keep `ENABLE_SCHEDULER=true` unless intentionally disabling all background jobs.
- Keep `SCHEDULER_AUTOSTART=false` on normal web instances.
- Set `SCHEDULER_AUTOSTART=true` on exactly one dedicated instance/process only.

This prevents duplicate escalation/retraining runs across multiple web workers.

## 6. Health Endpoint

`GET /health` now returns:

- app status (`healthy` or `degraded`)
- environment and configured base URL
- DB connectivity details
- ML model loaded state
- scheduler runtime state

Status code behavior:

- `200`: app is up and DB is reachable
- `503`: DB connectivity check failed

## 7. Local Development Profile

Suggested local values:

```env
FLASK_ENV=development
SECRET_KEY=local-dev-secret
APP_BASE_URL=http://localhost:8000
DATABASE_URL=sqlite:///grievance.db
DEMO_EMAIL_MODE=false
DEMO_SMS_MODE=false
AUTO_CREATE_TABLES=false
```

Run locally:

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m flask --app backend.app:create_app db upgrade
python manage.py seed
python run.py
```

## 8. GitHub Pages Frontend Mirror

`docs/` mirrors `frontend/` and uses the same runtime UI logic.

- It still needs a reachable backend API.
- API base is resolved via `runtime-config.js` (or defaults to Render backend on `github.io`).
