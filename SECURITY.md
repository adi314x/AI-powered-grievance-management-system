# Security & Architecture

This document clarifies the security posture for auditors and reviewers.

## Two Distinct Modes

| Mode | Path | Data Storage | Auth |
|------|------|--------------|------|
| **Full app** | `frontend/` + Flask backend | PostgreSQL/SQLite | JWT, server-side |
| **Static demo** | `docs/` | localStorage only | Simulated, client-only |

**The `docs/` folder is a standalone demo for GitHub Pages.** It does not use the backend. Any audit of "client-side persistence" or "JS-only auth" applies to `docs/` only.

---

## Full App (frontend/ + backend/) — Production Architecture

### Data & Persistence

- **Database:** SQLAlchemy with PostgreSQL (production) or SQLite (development)
- **Complaints, users, roles, lockouts, fraud flags:** Stored server-side only
- **localStorage usage:** JWT token + cached user object for display; language preference
- **Token strategy:** Access token + password-reset token + optional refresh token, each with explicit token type and expiry in payload

### Authentication & Authorization

- **JWT** issued by backend; validated on every protected request
- **Role checks:** Enforced server-side via `get_current_user_from_token()` and role guards
- **Lockout:** 3 failed logins = 24-hour lockout per email (server-side, `FailedLoginAttempt` table)
- **Passwords:** Werkzeug `generate_password_hash` / `check_password_hash` (PBKDF2)

### Validation & Sanitization

- **Input validation:** Server-side for all API inputs
- **XSS:** `bleach` sanitization via `SecurityFirewall.validate_input()` before persistence
- **SQL injection:** Parameterized queries (SQLAlchemy ORM); blocked patterns in firewall

### Rate Limiting & Throttling

- IP-based limits on login (10/5 min), registration (5/10 min), grievance submission (20/hour)
- IP blocking after repeated suspicious activity

### ML, Moderation & Trust Layer

- **Department Classification**: scikit-learn TF-IDF + Logistic Regression (~74% accuracy), runs server-side with confidence-aware manual triage fallback.
- **Keyword Moderation**: Server-side keyword/heuristic checks (threats, abuse, hate speech) using `ContentModerator`.
- **Submission Blocking**: Immediate rejection of extremely high-risk content (score >= 30) before persistence.
- **AI Image Detection**: Automated scanning of uploaded evidence for AI-generation signatures to prevent fraudulent claims.
- **SLA & Escalation**: Automated monitoring of response times with multi-level escalation for accountability.

### CSRF

- JWT in `Authorization` header (not cookies) — not vulnerable to classic CSRF
- No cookie-based session auth

### Session Storage Tradeoff (Current)

- Tokens are currently stored in `localStorage` for frontend simplicity and static-host compatibility.
- Tradeoff: `localStorage` is accessible to JavaScript, so any XSS can expose tokens.
- Mitigations currently in place: server-side sanitization, strict backend validation, and short-lived reset tokens.
- Recommended next step for higher-security deployments: migrate to HttpOnly secure cookies with CSRF protection.

---

## Known Gaps & Recommendations

1. **Frontend innerHTML:** User content is sanitized server-side before storage; frontend uses `innerHTML` for rendering. Consider escaping or using `textContent` for user-generated fields to defense-in-depth.

2. **Demo credentials:** `admin123`, `officer123` in README/seed — for development only. Rotate before any real deployment.

3. **CORS:** Currently `origins: "*"` in development. Restrict to specific domain in production.

4. **Audit logging:** Basic security logging exists; consider structured audit trail for compliance.

---

## For Auditors

- **Full app:** Run `python run.py` and use http://localhost:8000 (serves `frontend/`).
- **Static demo:** The `docs/` folder is for GitHub Pages only; it is not the production app.
- **Backend code:** See `backend/routes/`, `backend/security/`, `backend/services/`.
