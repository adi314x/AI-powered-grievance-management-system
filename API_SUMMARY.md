# API Summary

Base URL (local): `http://localhost:8000`

All API routes are JSON and are prefixed by one of:
- `/api/auth`
- `/api/grievances`
- `/api/admin`
- `/api` (public/add-on endpoints)

Authentication header for protected routes:

```http
Authorization: Bearer <access_token>
```

## Auth Endpoints (`/api/auth`)

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register citizen account |
| POST | `/api/auth/send-otp` | Public | Send OTP (email/phone) |
| POST | `/api/auth/verify-otp` | Public | Verify OTP |
| POST | `/api/auth/login` | Public | Login and get access token (and refresh token if enabled) |
| POST | `/api/auth/refresh-token` | Public | Exchange refresh token for new access token |
| POST | `/api/auth/forgot-password` | Public | Start password reset |
| POST | `/api/auth/verify-reset-otp` | Public | Verify reset OTP and get reset token |
| POST | `/api/auth/reset-password` | Public | Reset password with reset token |
| GET | `/api/auth/me` | Authenticated | Get current user profile |
| PUT | `/api/auth/profile/update` | Authenticated | Update profile fields with server validation |

## Grievance Endpoints (`/api/grievances`)

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/api/grievances/predict-department` | Authenticated | Predict department + confidence + image requirement |
| POST | `/api/grievances/submit` | Citizen | Submit grievance |
| GET | `/api/grievances/my-grievances` | Authenticated | List current user grievances |
| GET | `/api/grievances/<id>` | Authorized viewer | Get grievance details/timeline/comments |
| GET | `/api/grievances/department/<department>` | Officer/Admin | List department grievances |
| POST | `/api/grievances/<id>/update` | Officer/Admin | Add status update |
| GET | `/api/grievances/<id>/comments` | Authorized viewer | List comments |
| POST | `/api/grievances/<id>/comments` | Citizen/Officer/Admin (guarded) | Add comment |
| POST | `/api/grievances/<id>/report-fraud` | Officer | Create fraud report |
| GET | `/api/grievances/fraud-reports` | Admin | List fraud reports |
| POST | `/api/grievances/fraud-reports/<report_id>/action` | Admin | Fraud action (`verify`/`dismiss`/`suspend`) |
| POST | `/api/grievances/check-comment-escalations` | Admin | Run escalation check manually |
| POST | `/api/grievances/comments/<comment_id>/escalate` | Admin | Force manual escalation for a comment |

## Admin Endpoints (`/api/admin`)

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/api/admin/create-officer` | Admin | Create officer user |
| GET | `/api/admin/officers` | Admin | List officers |
| GET | `/api/admin/users` | Admin | List citizens + grievance counts |
| GET | `/api/admin/analytics` | Admin | Aggregated analytics |
| GET | `/api/admin/all-grievances` | Admin | Full grievance listing with complainant context |
| GET | `/api/admin/departments` | Authenticated | List known departments |
| POST | `/api/admin/assign-officer` | Admin | Assign officer to grievance |
| GET | `/api/admin/notifications` | Authenticated | List notifications |
| PUT | `/api/admin/notifications/<notification_id>/mark-read` | Authenticated owner | Mark notification read |
| PUT | `/api/admin/notifications/mark-all-read` | Authenticated | Mark all notifications read |
| POST | `/api/admin/retrain-model` | Admin | Trigger ML retraining |
| GET | `/api/admin/model-status` | Admin | Model runtime/training/correction metadata |
| POST | `/api/admin/reset-lockout/<email>` | Admin | Reset login lockout for user email |

## Public and Add-on Endpoints (`/api`)

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/public/stats` | Public | Public aggregate stats |
| GET | `/api/public/resolved-cases` | Public | Anonymized resolved grievance feed |
| POST | `/api/grievances/<id>/rate` | Authenticated owner | Submit grievance rating |
| GET | `/api/grievances/<id>/rating` | Authenticated owner | Fetch grievance rating |
| GET | `/api/grievances/<id>/qr` | Public | Tracking QR image |
| GET | `/api/admin/audit/export` | Admin | Export audit report (PDF or JSON fallback) |
| GET | `/api/admin/export/grievances` | Officer/Admin | Export grievances (Excel) |

## Health and Frontend

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/health` | Public | App, DB, ML, scheduler runtime health |
| GET | `/` | Public | Serves `frontend/index.html` |

## Error Shape Notes

Auth guard failures use a structured payload:

```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token",
  "code": "auth_invalid_token"
}
```

Other endpoint errors generally use:

```json
{ "error": "..." }
```
