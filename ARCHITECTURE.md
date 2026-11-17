# Architecture Overview

This document describes the production application architecture (`backend/` + `frontend/`).

## 1. Backend (Flask)

Main entry:
- `backend/app.py` (`create_app` factory)

Key backend modules:
- `backend/routes/auth.py` - auth, profile, password reset, token refresh
- `backend/routes/grievances.py` - grievance lifecycle, comments, fraud flows
- `backend/routes/admin.py` - officer/admin operations, assignment, analytics, model controls
- `backend/routes/addons.py` - public stats, resolved feed, exports, QR, ratings
- `backend/services/*` - email, classifier, retraining, scheduler, escalation, moderation
- `backend/security/*` - firewall, headers, audit service, request validation helpers

## 2. Frontend (Vanilla JS + HTML)

Served by Flask from `frontend/`.

Structure:
- `frontend/index.html`, `frontend/officer.html`, `frontend/admin.html`, `frontend/track.html` and auth/profile pages
- `frontend/app.js` - API wrapper, token/session helpers, shared utilities
- `frontend/js/pages/*` - modularized index page behavior (form + dashboard)
- `frontend/department-image-requirements.js` - frontend rule hints for evidence requirements
- Translation stack: `language-config.js`, `translations.js`, `simple-translator.js`, `language-selector-widget.js`

## 3. Authentication and Authorization

Token model:
- Access token (`token_type=access`)
- Refresh token (`token_type=refresh`, optional via config)
- Password reset token (`token_type=password_reset`)

Current storage model:
- Frontend stores tokens in `localStorage`.

Role model:
- `CITIZEN`, `OFFICER`, `ADMIN`
- Permission checks are enforced server-side in route guards and workflow helpers.

## 4. Grievance Workflow Engine

Submission path:
1. Citizen submits complaint text + location + images.
2. Classifier predicts department and confidence.
2b. Vision service classifies evidence images and checks for AI-generation signals (supporting evidence only).
3. Routing decision:
   - confidence >= threshold -> auto department assignment
   - confidence < threshold / model unavailable -> manual triage queue
4. Admin assigns officer (with department checks, except triage queue correction path).
5. Officer/admin update statuses and comments.
6. **SLA & Escalation Engine**:
   - Every grievance is assigned an `sla_deadline` based on department config (default 48h).
   - The `Background Scheduler` runs an escalation scan.
   - Overdue/breached cases trigger notifications and are marked as `sla_breached`.

## 5. Content Moderation & Trust Layer

Complaint text submitted by citizens passes through server-side validation and
the content-moderation service:
- **Keyword Moderation**: Detects configured threat, abuse, hate-speech, or
  personal-attack terms/patterns using `ContentModerator`. This is
  rule-based—not a trained moderation model.
- **Severity Scoring**: Scores of 30 or higher block submission. Lower-risk
  flagged content can generate an admin review notification.
- **Image Evidence Analysis**: At submission, `backend/services/image_ai_service.py`
  runs two ONNX models from `ml/artifacts/vision`:
  - `issue_classifier.onnx` — pothole / garbage / other
  - `ai_image_detector.onnx` — real / fake (CIFAKE, 32×32)
  Results are stored in `ai_detection_details`; a fake score at or above
  `VISION_AI_FLAG_THRESHOLD` (default `0.80`) sets `ai_image_detected` /
  `is_flagged` and notifies admins. Department suggestions require issue
  confidence at or above `VISION_ISSUE_CONFIDENCE_THRESHOLD` (default `0.60`).
  Text routing remains authoritative, and no case is auto-rejected from an
  image score alone.
- **Legacy Image Heuristics**: `AIImageDetector` metadata/EXIF checks remain
  available for auxiliary analysis but are not required for the live flow.

## 6. Fraud Lifecycle Management

1. **Reporting**: Officers can report a grievance they suspect is fraudulent.
2. **Review**: Admins review the fraud report and evidence.
3. **Resolution**:
   - **Verified**: Grievance is closed as "Fraud," and the user account is suspended.
   - **Dismissed**: Fraud report is cleared and grievance status is restored.
4. **Resilience**: Admins can later "Unsuspend" accounts with a documented audit trail.

Comment escalation:
- Citizen comments create officer notification + response deadline.
- Scheduler checks overdue comments and escalates to department officers/admin fallback.

## 5. ML Pipeline

Text artifacts:
- model: `ml/artifacts/model.joblib`
- vectorizer: `ml/artifacts/vectorizer.joblib`
- metadata: `ml/artifacts/train_metadata.json`

Vision artifacts:
- issue classifier: `ml/artifacts/vision/issue_classifier.onnx` (+ `.onnx.data`)
- AI-image detector: `ml/artifacts/vision/ai_image_detector.onnx` (+ `.onnx.data`)
- preprocessing/labels: matching `*_preprocess.json` / `*_labels.json`

Capabilities:
- Predict department with confidence and top candidates.
- Analyze uploaded evidence images with ONNX Runtime (CPU), without loading
  PyTorch in the Flask process.
- Expose runtime/model status via admin endpoint.
- Log department corrections for retraining feedback loop.
- Support manual retrain trigger + optional scheduled retraining.

## 6. Notifications and Email

Notification channels:
- In-app notifications persisted in DB (`Notification` model).
- Email notifications through centralized helper methods in `backend/services/email_service.py`.

Link generation:
- Uses `APP_BASE_URL` for canonical tracking/action links.

## 7. Database and Persistence

ORM:
- Flask-SQLAlchemy models in `backend/models.py` and `backend/models_addons.py`.

Migration:
- Flask-Migrate/Alembic (`migrations/`)
- Production path should always use migration upgrades, not `db.create_all()`.

Supported DB targets:
- Local: SQLite
- Production: PostgreSQL via `DATABASE_URL`

## 8. Background Jobs

Service:
- `backend/services/scheduler.py`

Jobs:
- Comment escalation checks (hourly loop)
- Optional scheduled model retraining

Operational guidance:
- Keep `SCHEDULER_AUTOSTART=false` on most app instances.
- Enable `SCHEDULER_AUTOSTART=true` on exactly one instance/process.

## 9. Health and Runtime Diagnostics

Endpoint:
- `GET /health`

Reports:
- App environment/base URL
- DB connectivity + dialect
- ML model loaded state
- Scheduler runtime status

Status behavior:
- `200` when DB is reachable
- `503` when DB check fails
## 10. Audit & Transparency

- **Security Audit Logs**: Track sensitive operations (suspensions, resets, role changes).
- **Public Dashboard**: Anonymized metrics and resolved case feeds for public accountability.
- **Citizen Timeline**: Full transparency for citizens to track every update and comment on their case.
