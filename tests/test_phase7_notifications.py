from datetime import datetime, timedelta

from backend.extensions import db
from backend.models import EscalationLog, Grievance, GrievanceComment, Notification, User, FraudReport
from backend.routes.auth import create_access_token
from backend.services.comment_escalation import check_and_escalate_comments
from backend.services.email_service import EmailService


def auth_headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def create_user(name, email, phone, role="CITIZEN", department=None, password="Password123"):
    user = User(
        name=name,
        email=email,
        phone=phone,
        role=role,
        department=department,
        email_verified=True,
        phone_verified=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def create_grievance(user_id, department, status="Assigned to Department", assigned_officer_id=None):
    grievance = Grievance(
        user_id=user_id,
        complaint_text="Persistent civic issue reported by resident.",
        predicted_department=department,
        assigned_department=department,
        status=status,
        assigned_officer_id=assigned_officer_id,
        location="Ward office main road",
    )
    db.session.add(grievance)
    db.session.commit()
    return grievance


def test_citizen_comment_creates_notification_and_uses_template_email(client, app, monkeypatch):
    with app.app_context():
        citizen = create_user("Citizen One", "phase7-citizen1@example.com", "9876530001")
        officer = create_user(
            "Officer One",
            "phase7-officer1@example.com",
            "9876530002",
            role="OFFICER",
            department="Water Supply",
        )
        grievance = create_grievance(citizen.id, "Water Supply", assigned_officer_id=officer.id)
        citizen_id = citizen.id
        grievance_id = grievance.id
        officer_id = officer.id

    captured = []

    def capture_comment_email(**kwargs):
        captured.append(kwargs)
        return True

    monkeypatch.setattr(EmailService, "send_citizen_comment_alert", staticmethod(capture_comment_email))

    response = client.post(
        f"/api/grievances/{grievance_id}/comments",
        json={"comment_text": "No one has visited yet. Please respond urgently."},
        headers=auth_headers(citizen_id),
    )
    assert response.status_code == 201
    assert len(captured) == 1
    assert captured[0]["grievance_id"] == grievance_id

    with app.app_context():
        saved_comment = GrievanceComment.query.filter_by(
            grievance_id=grievance_id,
            user_id=citizen_id,
        ).first()
        assert saved_comment is not None
        assert saved_comment.notified_officer_id == officer_id
        assert saved_comment.response_deadline is not None

        notification = Notification.query.filter_by(
            user_id=officer_id,
            related_grievance_id=grievance_id,
            notification_type="comment",
        ).first()
        assert notification is not None


def test_officer_reply_uses_standardized_citizen_email(client, app, monkeypatch):
    with app.app_context():
        citizen = create_user("Citizen Two", "phase7-citizen2@example.com", "9876530003")
        officer = create_user(
            "Officer Two",
            "phase7-officer2@example.com",
            "9876530004",
            role="OFFICER",
            department="Roads and Public Works",
        )
        grievance = create_grievance(citizen.id, "Roads and Public Works", assigned_officer_id=officer.id)
        officer_id = officer.id
        grievance_id = grievance.id
        citizen_email = citizen.email

    captured = []

    def capture_reply_email(**kwargs):
        captured.append(kwargs)
        return True

    monkeypatch.setattr(EmailService, "send_officer_reply_alert", staticmethod(capture_reply_email))

    response = client.post(
        f"/api/grievances/{grievance_id}/comments",
        json={"comment_text": "Work order approved. Team will fix the road this evening."},
        headers=auth_headers(officer_id),
    )
    assert response.status_code == 201
    assert len(captured) == 1
    assert captured[0]["citizen_email"] == citizen_email
    assert captured[0]["grievance_id"] == grievance_id


def test_escalation_persists_even_if_escalation_emails_fail(app, monkeypatch):
    with app.app_context():
        citizen = create_user("Citizen Three", "phase7-citizen3@example.com", "9876530005")
        primary_officer = create_user(
            "Primary Officer",
            "phase7-primary@example.com",
            "9876530006",
            role="OFFICER",
            department="Electricity",
        )
        backup_officer = create_user(
            "Backup Officer",
            "phase7-backup@example.com",
            "9876530007",
            role="OFFICER",
            department="Electricity",
        )
        grievance = create_grievance(
            citizen.id,
            "Electricity",
            assigned_officer_id=primary_officer.id,
        )
        comment = GrievanceComment(
            grievance_id=grievance.id,
            user_id=citizen.id,
            comment_text="Still no update after repeated follow-up.",
            user_role="CITIZEN",
            user_name=citizen.name,
            notified_officer_id=primary_officer.id,
            notification_sent_at=datetime.utcnow() - timedelta(days=2),
            response_deadline=datetime.utcnow() - timedelta(hours=3),
            created_at=datetime.utcnow() - timedelta(days=2),
            escalated=False,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = comment.id
        grievance_id = grievance.id
        backup_officer_id = backup_officer.id

        def failing_email(**kwargs):
            raise RuntimeError("Email transport unavailable")

        monkeypatch.setattr(EmailService, "send_escalation_alert", staticmethod(failing_email))
        monkeypatch.setattr(EmailService, "send_escalation_notice_to_officer", staticmethod(failing_email))

        escalated_count = check_and_escalate_comments()
        assert escalated_count == 1

        saved_comment = GrievanceComment.query.get(comment_id)
        assert saved_comment.escalated is True
        assert saved_comment.escalated_to_officer_id == backup_officer_id

        notification = Notification.query.filter_by(
            user_id=backup_officer_id,
            related_grievance_id=grievance_id,
            notification_type="escalation",
        ).first()
        assert notification is not None

        escalation_log = EscalationLog.query.filter_by(grievance_id=grievance_id, escalation_type="auto").first()
        assert escalation_log is not None


def test_fraud_review_and_actions_create_notifications_and_emails(client, app, monkeypatch):
    with app.app_context():
        admin = create_user("Admin One", "phase7-admin1@example.com", "9876530008", role="ADMIN")
        citizen = create_user("Citizen Four", "phase7-citizen4@example.com", "9876530009")
        officer = create_user(
            "Officer Three",
            "phase7-officer3@example.com",
            "9876530010",
            role="OFFICER",
            department="Sanitation and Waste Management",
        )
        grievance = create_grievance(
            citizen.id,
            "Sanitation and Waste Management",
            assigned_officer_id=officer.id,
        )
        admin_id = admin.id
        officer_id = officer.id
        grievance_id = grievance.id
        citizen_id = citizen.id

    fraud_report_calls = []
    fraud_notice_calls = []
    warning_calls = []
    suspension_calls = []

    monkeypatch.setattr(
        EmailService,
        "send_fraud_report_alert",
        staticmethod(lambda **kwargs: fraud_report_calls.append(kwargs) or True),
    )
    monkeypatch.setattr(
        EmailService,
        "send_fraud_review_notice",
        staticmethod(lambda **kwargs: fraud_notice_calls.append(kwargs) or True),
    )
    monkeypatch.setattr(
        EmailService,
        "send_account_warning_email",
        staticmethod(lambda **kwargs: warning_calls.append(kwargs) or True),
    )
    monkeypatch.setattr(
        EmailService,
        "send_account_suspension_email",
        staticmethod(lambda **kwargs: suspension_calls.append(kwargs) or True),
    )

    report_response = client.post(
        f"/api/grievances/{grievance_id}/report-fraud",
        json={
            "fraud_type": "false_complaint",
            "description": "Site visit found no such issue in the reported location.",
            "site_visit_notes": "Verified with geo-tagged inspection.",
        },
        headers=auth_headers(officer_id),
    )
    assert report_response.status_code == 201
    assert len(fraud_report_calls) >= 1
    assert len(fraud_notice_calls) >= 1

    with app.app_context():
        admin_notification = Notification.query.filter_by(
            user_id=admin_id,
            related_grievance_id=grievance_id,
            notification_type="fraud_report",
        ).first()
        complainant_notification = Notification.query.filter_by(
            user_id=citizen_id,
            related_grievance_id=grievance_id,
            notification_type="fraud_warning",
        ).first()
        assert admin_notification is not None
        assert complainant_notification is not None

        report = FraudReport.query.filter_by(grievance_id=grievance_id).first()
        report_id = report.id

    verify_response = client.post(
        f"/api/grievances/fraud-reports/{report_id}/action",
        json={"action": "verify", "admin_notes": "First confirmed fraudulent complaint."},
        headers=auth_headers(admin_id),
    )
    assert verify_response.status_code == 200
    assert len(warning_calls) == 1

    with app.app_context():
        second_report = FraudReport(
            grievance_id=grievance_id,
            reported_by_officer_id=officer_id,
            complainant_user_id=citizen_id,
            fraud_type="duplicate",
            description="Repeated fake complaint",
            status="Pending",
        )
        db.session.add(second_report)
        db.session.commit()
        second_report_id = second_report.id

    suspend_response = client.post(
        f"/api/grievances/fraud-reports/{second_report_id}/action",
        json={"action": "suspend", "admin_notes": "Repeated verified fraudulent submissions."},
        headers=auth_headers(admin_id),
    )
    assert suspend_response.status_code == 200
    assert len(suspension_calls) == 1

    with app.app_context():
        citizen = User.query.get(citizen_id)
        assert citizen.account_suspended is True
        suspension_notification = Notification.query.filter_by(
            user_id=citizen_id,
            notification_type="account_suspended",
        ).first()
        assert suspension_notification is not None

