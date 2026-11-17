"""Regression tests for functional fixes in the grievance workflow."""

from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from backend.extensions import db
from backend.models import Grievance, GrievanceUpdate, Notification, User
from backend.routes.auth import create_access_token
from backend.services import scheduler as scheduler_module


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def auth_headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def create_user(name, email, phone, role="CITIZEN", department=None):
    user = User(
        name=name,
        email=email,
        phone=phone,
        role=role,
        department=department,
        email_verified=True,
        phone_verified=True,
    )
    user.set_password("Password123")
    db.session.add(user)
    db.session.commit()
    return user


def create_grievance(
    user_id,
    department,
    status="Assigned to Department",
    assigned_officer_id=None,
    created_at=None,
    updated_at=None,
    requires_manual_triage=False,
):
    grievance = Grievance(
        user_id=user_id,
        complaint_text="Persistent civic issue reported by a resident for testing.",
        predicted_department=department,
        assigned_department=department,
        status=status,
        assigned_officer_id=assigned_officer_id,
        requires_manual_triage=requires_manual_triage,
        location="Ward office main road",
    )
    if created_at is not None:
        grievance.created_at = created_at
    if updated_at is not None:
        grievance.updated_at = updated_at
    db.session.add(grievance)
    db.session.commit()
    return grievance


# ── Public stats / resolution metrics ────────────────────────────────────────

def test_public_stats_uses_resolution_update_timestamp(client, app):
    with app.app_context():
        admin = create_user("Metric Admin", "metric-admin@example.com", "9900000001", role="ADMIN")
        citizen = create_user("Metric Citizen", "metric-citizen@example.com", "9900000002")
        now = datetime.utcnow()
        grievance = create_grievance(
            citizen.id,
            "Water Supply",
            status="Resolved",
            created_at=now - timedelta(days=6),
            updated_at=now,
        )
        db.session.add(
            GrievanceUpdate(
                grievance_id=grievance.id,
                status="Resolved",
                message="Pipeline repaired and water supply restored.",
                updated_by_role="OFFICER",
                updated_by_name="Water Officer",
                timestamp=now - timedelta(days=2),
            )
        )
        create_grievance(citizen.id, "Electricity", status="Under Progress")
        db.session.commit()
        admin_id = admin.id

    public_response = client.get("/api/public/stats")
    assert public_response.status_code == 200
    public_payload = public_response.get_json()
    assert public_payload["total_grievances"] == 2
    assert public_payload["resolved"] == 1
    assert public_payload["pending"] == 1
    assert public_payload["avg_resolution_days"] == 4.0

    resolved_response = client.get("/api/public/resolved-cases")
    assert resolved_response.status_code == 200
    resolved_case = resolved_response.get_json()["cases"][0]
    resolved_at = datetime.fromisoformat(resolved_case["resolved_at"])
    assert abs((resolved_at - (now - timedelta(days=2))).total_seconds()) < 1

    analytics_response = client.get("/api/admin/analytics", headers=auth_headers(admin_id))
    assert analytics_response.status_code == 200
    assert analytics_response.get_json()["avg_resolution_time_days"] == 4.0


# ── Rating and audit export validation ───────────────────────────────────────

def test_rating_rejects_missing_or_invalid_payload(client, app):
    with app.app_context():
        citizen = create_user("Rating Citizen", "rating-citizen@example.com", "9900000011")
        grievance = create_grievance(citizen.id, "Sanitation and Waste Management", status="Resolved")
        citizen_id = citizen.id
        grievance_id = grievance.id

    missing_body = client.post(
        f"/api/grievances/{grievance_id}/rate",
        headers=auth_headers(citizen_id),
    )
    assert missing_body.status_code == 400

    missing_rating = client.post(
        f"/api/grievances/{grievance_id}/rate",
        json={},
        headers=auth_headers(citizen_id),
    )
    assert missing_rating.status_code == 400

    invalid_rating = client.post(
        f"/api/grievances/{grievance_id}/rate",
        json={"rating": True},
        headers=auth_headers(citizen_id),
    )
    assert invalid_rating.status_code == 400

    invalid_optional = client.post(
        f"/api/grievances/{grievance_id}/rate",
        json={"rating": 4, "resolution_speed": 9},
        headers=auth_headers(citizen_id),
    )
    assert invalid_optional.status_code == 400

    valid = client.post(
        f"/api/grievances/{grievance_id}/rate",
        json={
            "rating": 4,
            "feedback_text": "Quick response and clear communication.",
            "resolution_speed": 4,
            "officer_helpfulness": 5,
        },
        headers=auth_headers(citizen_id),
    )
    assert valid.status_code == 200


def test_audit_export_handles_invalid_days_without_500(client, app):
    with app.app_context():
        admin = create_user("Audit Admin", "audit-admin@example.com", "9900000012", role="ADMIN")
        admin_id = admin.id

    invalid = client.get(
        "/api/admin/audit/export?days=not-a-number",
        headers=auth_headers(admin_id),
    )
    assert invalid.status_code == 200

    out_of_range = client.get(
        "/api/admin/audit/export?days=0",
        headers=auth_headers(admin_id),
    )
    assert out_of_range.status_code == 200

    valid = client.get(
        "/api/admin/audit/export?days=7",
        headers=auth_headers(admin_id),
    )
    assert valid.status_code == 200


# ── Officer queue ownership data ─────────────────────────────────────────────

def test_officer_queue_exposes_assigned_officer_name(client, app):
    with app.app_context():
        citizen = create_user("Queue Citizen", "queue-citizen@example.com", "9900000021")
        officer = create_user(
            "Queue Officer",
            "queue-officer@example.com",
            "9900000022",
            role="OFFICER",
            department="Water Supply",
        )
        other_officer = create_user(
            "Other Officer",
            "other-officer@example.com",
            "9900000023",
            role="OFFICER",
            department="Water Supply",
        )
        grievance = create_grievance(
            citizen.id,
            "Water Supply",
            assigned_officer_id=other_officer.id,
        )
        officer_id = officer.id
        other_officer_id = other_officer.id
        grievance_id = grievance.id

    response = client.get(
        f"/api/grievances/department/{quote('Water Supply')}",
        headers=auth_headers(officer_id),
    )
    assert response.status_code == 200
    grievance_data = next(
        item for item in response.get_json()["grievances"] if item["id"] == grievance_id
    )
    assert grievance_data["assigned_officer_id"] == other_officer_id
    assert grievance_data["assigned_officer_name"] == "Other Officer"


# ── Moderation flag and notification routing ─────────────────────────────────

def test_moderation_sets_flag_and_notifies_admin(client, app, monkeypatch):
    with app.app_context():
        admin = create_user("Moderation Admin", "moderation-admin@example.com", "9900000031", role="ADMIN")
        citizen = create_user("Moderation Citizen", "moderation-citizen@example.com", "9900000032")
        admin_id = admin.id
        citizen_id = citizen.id

    moderation = {
        "is_safe": True,
        "score": 20,
        "severity": "warning",
        "flags": [{"type": "abusive", "severity": "medium"}],
    }
    monkeypatch.setattr(
        "backend.routes.grievances.ContentModerator.moderate_content",
        lambda *args, **kwargs: moderation,
    )
    monkeypatch.setattr(
        "backend.routes.grievances.classifier.predict_with_confidence",
        lambda *args, **kwargs: {
            "department": "Education",
            "confidence": 0.9,
            "source": "mock",
            "model_loaded": True,
        },
    )

    response = client.post(
        "/api/grievances/submit",
        json={
            "complaint_text": "This complaint contains mildly inappropriate wording for testing.",
            "location": "Detailed location for validation purposes.",
        },
        headers=auth_headers(citizen_id),
    )
    assert response.status_code == 201

    with app.app_context():
        grievance = Grievance.query.filter_by(user_id=citizen_id).order_by(Grievance.id.desc()).first()
        assert grievance.is_flagged is True
        notification = Notification.query.filter_by(
            user_id=admin_id,
            related_grievance_id=grievance.id,
            notification_type="content_moderation",
        ).first()
        assert notification is not None


def test_manual_triage_and_moderation_notifications_both_created(client, app, monkeypatch):
    with app.app_context():
        admin = create_user("Triage Admin", "triage-admin@example.com", "9900000041", role="ADMIN")
        citizen = create_user("Triage Citizen", "triage-citizen@example.com", "9900000042")
        admin_id = admin.id
        citizen_id = citizen.id

    moderation = {
        "is_safe": True,
        "score": 20,
        "severity": "warning",
        "flags": [{"type": "abusive", "severity": "medium"}],
    }
    monkeypatch.setattr(
        "backend.routes.grievances.ContentModerator.moderate_content",
        lambda *args, **kwargs: moderation,
    )
    monkeypatch.setattr(
        "backend.routes.grievances.classifier.predict_with_confidence",
        lambda *args, **kwargs: {
            "department": "Education",
            "confidence": 0.1,
            "source": "mock",
            "model_loaded": True,
        },
    )

    response = client.post(
        "/api/grievances/submit",
        json={
            "complaint_text": "This complaint is routed to manual triage during the test.",
            "location": "Detailed location for validation purposes.",
        },
        headers=auth_headers(citizen_id),
    )
    assert response.status_code == 201

    with app.app_context():
        grievance = Grievance.query.filter_by(user_id=citizen_id).order_by(Grievance.id.desc()).first()
        assert grievance.requires_manual_triage is True
        triage_notification = Notification.query.filter_by(
            user_id=admin_id,
            related_grievance_id=grievance.id,
            notification_type="triage_review",
        ).first()
        moderation_notification = Notification.query.filter_by(
            user_id=admin_id,
            related_grievance_id=grievance.id,
            notification_type="content_moderation",
        ).first()
        assert triage_notification is not None
        assert moderation_notification is not None


# ── Status and reply notifications ──────────────────────────────────────────

def test_status_update_creates_citizen_notification(client, app):
    with app.app_context():
        citizen = create_user("Status Citizen", "status-citizen@example.com", "9900000051")
        officer = create_user(
            "Status Officer",
            "status-officer@example.com",
            "9900000052",
            role="OFFICER",
            department="Roads and Public Works",
        )
        grievance = create_grievance(
            citizen.id,
            "Roads and Public Works",
            assigned_officer_id=officer.id,
        )
        citizen_id = citizen.id
        officer_id = officer.id
        grievance_id = grievance.id

    response = client.post(
        f"/api/grievances/{grievance_id}/update",
        json={
            "status": "Under Progress",
            "message": "Field team has inspected the road and work has started.",
        },
        headers=auth_headers(officer_id),
    )
    assert response.status_code == 200

    with app.app_context():
        notification = Notification.query.filter_by(
            user_id=citizen_id,
            related_grievance_id=grievance_id,
            notification_type="status_update",
        ).first()
        assert notification is not None


def test_officer_reply_creates_citizen_notification(client, app):
    with app.app_context():
        citizen = create_user("Reply Citizen", "reply-citizen@example.com", "9900000061")
        officer = create_user(
            "Reply Officer",
            "reply-officer@example.com",
            "9900000062",
            role="OFFICER",
            department="Electricity",
        )
        grievance = create_grievance(
            citizen.id,
            "Electricity",
            assigned_officer_id=officer.id,
        )
        citizen_id = citizen.id
        officer_id = officer.id
        grievance_id = grievance.id

    response = client.post(
        f"/api/grievances/{grievance_id}/comments",
        json={"comment_text": "Transformer replacement is scheduled for tomorrow morning."},
        headers=auth_headers(officer_id),
    )
    assert response.status_code == 201

    with app.app_context():
        notification = Notification.query.filter_by(
            user_id=citizen_id,
            related_grievance_id=grievance_id,
            notification_type="comment_reply",
        ).first()
        assert notification is not None


# ── Scheduler cadence and first-run behavior ────────────────────────────────

def test_should_retrain_uses_persisted_metadata(tmp_path, monkeypatch):
    metadata_path = tmp_path / "train_metadata.json"
    monkeypatch.setattr(scheduler_module.Config, "ENABLE_SCHEDULED_RETRAIN", True)
    monkeypatch.setattr(scheduler_module.Config, "MODEL_METADATA_PATH", str(metadata_path))
    monkeypatch.setattr(scheduler_module, "RETRAIN_INTERVAL_HOURS", 168)

    now = datetime(2026, 1, 8, 12, 0, 0)
    assert scheduler_module._should_retrain(now) is False

    metadata_path.write_text(
        '{"trained_at_utc": "2025-12-31T12:00:00"}',
        encoding="utf-8",
    )
    assert scheduler_module._should_retrain(now) is True

    metadata_path.write_text(
        '{"trained_at_utc": "2026-01-08T11:00:00"}',
        encoding="utf-8",
    )
    assert scheduler_module._should_retrain(now) is False


def test_scheduler_runs_cycle_before_sleeping(app, monkeypatch):
    calls = []
    scheduler = scheduler_module.BackgroundScheduler(app)
    scheduler.running = True
    monkeypatch.setattr(scheduler, "_run_once", lambda: calls.append("cycle"))

    def fake_sleep(seconds):
        calls.append(("sleep", seconds))
        scheduler.running = False

    monkeypatch.setattr(scheduler_module.time, "sleep", fake_sleep)
    scheduler._run_scheduler()

    assert calls[0] == "cycle"
    assert calls[1] == ("sleep", 3600)


def test_scheduler_run_once_executes_hourly_tasks(app, monkeypatch):
    calls = []
    monkeypatch.setattr(
        scheduler_module,
        "check_and_escalate_comments",
        lambda: calls.append("comments") or 0,
    )
    monkeypatch.setattr(
        scheduler_module,
        "scan_sla_breaches",
        lambda: calls.append("sla") or 0,
    )
    monkeypatch.setattr(scheduler_module, "_should_retrain", lambda: False)

    scheduler = scheduler_module.BackgroundScheduler(app)
    scheduler._run_once()

    assert calls == ["comments", "sla"]


# ── Frontend wiring checks ──────────────────────────────────────────────────

def test_admin_manual_triage_controls_are_present():
    html = (FRONTEND_DIR / "admin.html").read_text(encoding="utf-8")
    assert "Manual Review Required" in html
    assert "assignDepartmentSelect" in html
    assert "requires_manual_triage" in html


def test_officer_queue_hides_update_for_other_officers():
    html = (FRONTEND_DIR / "officer.html").read_text(encoding="utf-8")
    assert "assigned_officer_name" in html
    assert "assignedToOtherOfficer" in html
    assert "view only" in html


def test_track_qr_and_chatbot_use_api_resolver():
    track_html = (FRONTEND_DIR / "track.html").read_text(encoding="utf-8")
    chatbot_js = (FRONTEND_DIR / "js" / "chatbot.js").read_text(encoding="utf-8")
    assert "resolveApiUrl(`/api/grievances/${grievanceId}/qr`)" in track_html
    assert "resolveApiUrl('/api/rag/query')" in chatbot_js
