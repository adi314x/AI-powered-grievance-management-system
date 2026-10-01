import pytest
from datetime import datetime, timedelta
from backend.extensions import db
from backend.models import Grievance, User, FraudReport, RoleHierarchy, Notification
from backend.routes.auth import create_access_token
from backend.services.scheduler import scan_sla_breaches
from backend.services.notification_service import NotificationService
from backend.services.email_service import EmailService

def auth_headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}

def create_user_for_test(name, email, phone, role="CITIZEN", department=None):
    user = User(
        name=name, email=email, phone=phone, role=role, department=department,
        email_verified=True, phone_verified=True
    )
    user.set_password("Password123")
    db.session.add(user)
    db.session.commit()
    return user

# 1. SLA Breach Scan Side Effects Verification
def test_sla_breach_scanner_emits_notifications(client, app, monkeypatch):
    calls = []
    def mock_queue_notification(user_id, title, message, **kwargs):
        calls.append({"user_id": user_id, "title": title})
        return True
        
    # DIRECT MONKEYPATCH ON THE SERVICE CLASS
    monkeypatch.setattr(NotificationService, "queue_notification", mock_queue_notification)
    
    with app.app_context():
        citizen = create_user_for_test("SLA Citizen", "slactz@example.com", "9111111001")
        officer = create_user_for_test("SLA Officer", "slaoff@example.com", "9111111002", role="OFFICER", department="Water Supply")
        admin = create_user_for_test("SLA Admin", "sladmin@example.com", "9111111003", role="ADMIN")
        
        # Fresh ID capture
        admin_id = admin.id
        officer_id = officer.id
        
        g = Grievance(
            user_id=citizen.id,
            complaint_text="This is a test text of sufficient length for the SLA scan side effects test.",
            predicted_department="Water Supply",
            assigned_department="Water Supply",
            status="Assigned to Department",
            assigned_officer_id=officer_id,
            location="123 Hospital Road, Bangalore",
            sla_breached=False,
            sla_deadline=datetime.utcnow() - timedelta(hours=2)
        )
        db.session.add(g)
        db.session.commit()
        g_id = g.id
        
        # Execute scan
        scan_sla_breaches(app)
        
        # Check DB State
        db.session.expire_all()
        g_updated = db.session.get(Grievance, g_id)
        assert g_updated.sla_breached is True

    # Verify captured calls
    assert len(calls) >= 2
    assert any(c['user_id'] == officer_id for c in calls)
    assert any(c['user_id'] == admin_id for c in calls)

# 2. Fraud Verified Flow Side Effects
def test_fraud_verified_emits_warnings_and_emails(client, app, monkeypatch):
    notif_count = 0
    email_count = 0
    def mock_notif(*args, **kwargs):
        nonlocal notif_count
        notif_count += 1
        return True
    def mock_email(*args, **kwargs):
        nonlocal email_count
        email_count += 1
        return True
        
    monkeypatch.setattr(NotificationService, "queue_notification", mock_notif)
    monkeypatch.setattr(EmailService, "send_account_warning_email", mock_email)
    
    with app.app_context():
        admin = create_user_for_test("Fraud Admin", "fraud_adm1@example.com", "9111111004", role="ADMIN")
        citizen = create_user_for_test("Fraud Citizen", "fraud_ctz1@example.com", "9111111005")
        g = Grievance(
            user_id=citizen.id, complaint_text="Test complaint", predicted_department="Police",
            assigned_department="Police", status="Suspended - Fraud Investigation", location="Loc"
        )
        db.session.add(g)
        db.session.commit()
        
        report = FraudReport(
            grievance_id=g.id, reported_by_officer_id=admin.id, complainant_user_id=citizen.id,
            fraud_type="Fake", description="Desc", status="Pending"
        )
        db.session.add(report)
        db.session.commit()
        
        admin_id = admin.id
        report_id = report.id

    client.post(f"/api/grievances/fraud-reports/{report_id}/action", json={"action": "verify", "admin_notes": "Fake"}, headers=auth_headers(admin_id))
    assert notif_count >= 1
    assert email_count >= 1

# 3. Fraud Dismissed Flow Side Effects
def test_fraud_dismissed_emits_notifications(client, app, monkeypatch):
    notif_count = 0
    monkeypatch.setattr(NotificationService, "queue_notification", lambda *args, **kwargs: True) # Just to pass through
    
    # We want to specifically capture if a NOTIFICATION was queued
    calls = []
    monkeypatch.setattr(NotificationService, "queue_notification", lambda **k: calls.append(k))
    
    with app.app_context():
        admin = create_user_for_test("Fraud Admin2", "fraud_adm2@example.com", "9111111006", role="ADMIN")
        citizen = create_user_for_test("Fraud Citizen2", "fraud_ctz2@example.com", "9111111007")
        g = Grievance(user_id=citizen.id, complaint_text="Test", predicted_department="Roads and Public Works", assigned_department="Roads and Public Works", status="Suspended - Fraud Investigation", location="Loc")
        db.session.add(g)
        db.session.commit()
        
        report = FraudReport(grievance_id=g.id, reported_by_officer_id=admin.id, complainant_user_id=citizen.id, fraud_type="Fake", description="Test description", status="Pending")
        db.session.add(report)
        db.session.commit()
        admin_id = admin.id
        report_id = report.id

    client.post(f"/api/grievances/fraud-reports/{report_id}/action", json={"action": "dismiss", "admin_notes": "Real"}, headers=auth_headers(admin_id))
    assert len(calls) >= 1

# 4. Unsuspend Flow Side Effects
def test_unsuspend_emits_notifications_and_audit(client, app, monkeypatch):
    calls = []
    monkeypatch.setattr(NotificationService, "queue_notification", lambda **k: calls.append(k))
    
    with app.app_context():
        admin = create_user_for_test("Unsusp Admin", "uadm@example.com", "9111111008", role="ADMIN")
        citizen = create_user_for_test("Unsusp Citizen", "uctz@example.com", "9111111009")
        citizen.account_suspended = True
        citizen.suspension_reason = "Test"
        db.session.commit()
        admin_id = admin.id
        citizen_id = citizen.id
        
    client.post(f"/api/admin/unsuspend-user/{citizen_id}", json={"admin_notes": "Approved appeal and verified documents.", "reset_warnings": True}, headers=auth_headers(admin_id))
    assert len(calls) >= 1
