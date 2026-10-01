from datetime import datetime, timedelta

from backend.extensions import db
from backend.models import (
    EscalationLog,
    Grievance,
    GrievanceComment,
    GrievanceUpdate,
    Notification,
    User,
)
from backend.routes.auth import create_access_token
from backend.services.comment_escalation import (
    check_and_escalate_comments,
    escalate_comment_manually,
)


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
        complaint_text="Water leakage near apartment entrance for the last five days.",
        predicted_department=department,
        assigned_department=department,
        status=status,
        assigned_officer_id=assigned_officer_id,
        location="Block C Main Road",
    )
    db.session.add(grievance)
    db.session.commit()
    return grievance


def test_admin_assign_officer_requires_matching_department(client, app):
    with app.app_context():
        admin = create_user("Admin One", "admin-phase4@example.com", "9876511001", role="ADMIN")
        citizen = create_user("Citizen One", "citizen-phase4@example.com", "9876511002")
        wrong_dept_officer = create_user(
            "Officer Mismatch",
            "officer-mismatch@example.com",
            "9876511003",
            role="OFFICER",
            department="Electricity",
        )
        grievance = create_grievance(citizen.id, "Water Supply")
        admin_id = admin.id
        grievance_id = grievance.id
        officer_id = wrong_dept_officer.id

    response = client.post(
        "/api/admin/assign-officer",
        json={"grievance_id": grievance_id, "officer_id": officer_id},
        headers=auth_headers(admin_id),
    )
    assert response.status_code == 400
    assert "department mismatch" in response.get_json()["error"].lower()

    with app.app_context():
        grievance = Grievance.query.get(grievance_id)
        assert grievance.assigned_officer_id is None


def test_officer_cannot_update_grievance_assigned_to_another_officer(client, app):
    with app.app_context():
        citizen = create_user("Citizen Two", "citizen-two-phase4@example.com", "9876511004")
        assigned_officer = create_user(
            "Assigned Officer",
            "assigned-officer@example.com",
            "9876511005",
            role="OFFICER",
            department="Roads and Public Works",
        )
        other_officer = create_user(
            "Other Officer",
            "other-officer@example.com",
            "9876511006",
            role="OFFICER",
            department="Roads and Public Works",
        )
        grievance = create_grievance(
            citizen.id,
            "Roads and Public Works",
            assigned_officer_id=assigned_officer.id,
        )
        other_officer_id = other_officer.id
        grievance_id = grievance.id

    response = client.post(
        f"/api/grievances/{grievance_id}/update",
        json={"status": "Under Progress", "message": "Work order issued for repair team."},
        headers=auth_headers(other_officer_id),
    )
    assert response.status_code == 403
    assert "assigned to another officer" in response.get_json()["error"].lower()

    with app.app_context():
        update = GrievanceUpdate.query.filter_by(
            grievance_id=grievance_id,
            status="Under Progress",
        ).first()
        assert update is None


def test_officer_comment_claims_unassigned_grievance(client, app):
    with app.app_context():
        citizen = create_user("Citizen Three", "citizen-three-phase4@example.com", "9876511007")
        officer = create_user(
            "Officer Claim",
            "officer-claim@example.com",
            "9876511008",
            role="OFFICER",
            department="Water Supply",
        )
        grievance = create_grievance(citizen.id, "Water Supply", assigned_officer_id=None)
        grievance_id = grievance.id
        officer_id = officer.id

    response = client.post(
        f"/api/grievances/{grievance_id}/comments",
        json={"comment_text": "Inspection scheduled. We will visit by tomorrow morning."},
        headers=auth_headers(officer_id),
    )
    assert response.status_code == 201

    with app.app_context():
        grievance = Grievance.query.get(grievance_id)
        assert grievance.assigned_officer_id == officer_id


def test_officer_cannot_report_fraud_when_case_assigned_to_other_officer(client, app):
    with app.app_context():
        citizen = create_user("Citizen Four", "citizen-four-phase4@example.com", "9876511009")
        assigned_officer = create_user(
            "Assigned Fraud Officer",
            "assigned-fraud-officer@example.com",
            "9876511010",
            role="OFFICER",
            department="Sanitation and Waste Management",
        )
        other_officer = create_user(
            "Other Fraud Officer",
            "other-fraud-officer@example.com",
            "9876511011",
            role="OFFICER",
            department="Sanitation and Waste Management",
        )
        grievance = create_grievance(
            citizen.id,
            "Sanitation and Waste Management",
            assigned_officer_id=assigned_officer.id,
        )
        grievance_id = grievance.id
        other_officer_id = other_officer.id

    response = client.post(
        f"/api/grievances/{grievance_id}/report-fraud",
        json={
            "fraud_type": "false_complaint",
            "description": "No garbage issue found during site visit.",
            "site_visit_notes": "Location verified and found clean.",
        },
        headers=auth_headers(other_officer_id),
    )
    assert response.status_code == 403
    assert "another officer" in response.get_json()["error"].lower()


def test_overdue_comment_escalates_to_department_officer_and_logs(client, app):
    with app.app_context():
        citizen = create_user("Citizen Five", "citizen-five-phase4@example.com", "9876511012")
        primary_officer = create_user(
            "Primary Officer",
            "primary-officer@example.com",
            "9876511013",
            role="OFFICER",
            department="Electricity",
        )
        backup_officer = create_user(
            "Backup Officer",
            "backup-officer@example.com",
            "9876511014",
            role="OFFICER",
            department="Electricity",
        )
        create_user("Admin Two", "admin-two-phase4@example.com", "9876511015", role="ADMIN")
        grievance = create_grievance(
            citizen.id,
            "Electricity",
            assigned_officer_id=primary_officer.id,
        )
        comment = GrievanceComment(
            grievance_id=grievance.id,
            user_id=citizen.id,
            comment_text="Power outage still unresolved. Please update.",
            user_role="CITIZEN",
            user_name=citizen.name,
            notified_officer_id=primary_officer.id,
            notification_sent_at=datetime.utcnow() - timedelta(days=2),
            response_deadline=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow() - timedelta(days=2),
            escalated=False,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = comment.id
        grievance_id = grievance.id
        primary_officer_id = primary_officer.id
        backup_officer_id = backup_officer.id

        escalated_count = check_and_escalate_comments()
        assert escalated_count == 1

        saved_comment = GrievanceComment.query.get(comment_id)
        assert saved_comment.escalated is True
        assert saved_comment.escalated_to_officer_id == backup_officer_id

        escalation_notification = Notification.query.filter_by(
            user_id=backup_officer_id,
            related_grievance_id=grievance_id,
            notification_type="escalation",
        ).first()
        assert escalation_notification is not None

        escalation_log = EscalationLog.query.filter_by(grievance_id=grievance_id).first()
        assert escalation_log is not None
        assert escalation_log.from_officer_id == primary_officer_id
        assert escalation_log.to_officer_id == backup_officer_id
        assert escalation_log.escalation_type == "auto"


def test_manual_escalation_falls_back_to_admin_when_no_department_officer(app):
    with app.app_context():
        citizen = create_user("Citizen Six", "citizen-six-phase4@example.com", "9876511016")
        primary_officer = create_user(
            "Solo Officer",
            "solo-officer@example.com",
            "9876511017",
            role="OFFICER",
            department="Sanitation and Waste Management",
        )
        admin = create_user("Admin Three", "admin-three-phase4@example.com", "9876511018", role="ADMIN")
        grievance = create_grievance(
            citizen.id,
            "Sanitation and Waste Management",
            assigned_officer_id=primary_officer.id,
        )
        comment = GrievanceComment(
            grievance_id=grievance.id,
            user_id=citizen.id,
            comment_text="Mosquito issue remains unresolved near the lake area.",
            user_role="CITIZEN",
            user_name=citizen.name,
            notified_officer_id=primary_officer.id,
            notification_sent_at=datetime.utcnow() - timedelta(days=1),
            response_deadline=datetime.utcnow() - timedelta(hours=1),
            created_at=datetime.utcnow() - timedelta(days=1),
            escalated=False,
        )
        db.session.add(comment)
        db.session.commit()

        result = escalate_comment_manually(comment.id)
        assert result["success"] is True

        saved_comment = GrievanceComment.query.get(comment.id)
        assert saved_comment.escalated is True
        assert saved_comment.escalated_to_officer_id == admin.id

        manual_log = EscalationLog.query.filter_by(
            grievance_id=grievance.id,
            escalation_type="manual",
        ).first()
        assert manual_log is not None
        assert manual_log.to_officer_id == admin.id

