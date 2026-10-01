from backend.extensions import db
from backend.config import Config
from backend.models import Grievance, GrievanceComment, GrievanceUpdate, Notification, User
from backend.routes.auth import create_access_token, decode_token
from backend.services.email_service import EmailService
from backend.services.otp_service import OTPService


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


def create_grievance(user_id, department, status="Received", assigned_officer_id=None):
    grievance = Grievance(
        user_id=user_id,
        complaint_text="Streetlight near the main junction has not worked for several days.",
        predicted_department=department,
        assigned_department=department,
        status=status,
        assigned_officer_id=assigned_officer_id,
        location="Main Junction, Ward 11",
    )
    db.session.add(grievance)
    db.session.commit()
    return grievance


def test_register_then_login_succeeds(client):
    register_payload = {
        "name": "Fresh Citizen",
        "email": "fresh.citizen@example.com",
        "phone": "9876500999",
        "password": "FreshPass123",
        "date_of_birth": "1992-05-14",
        "gender": "Other",
    }
    register_response = client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    payload = login_response.get_json()
    assert payload["token"]
    assert payload["user"]["email"] == register_payload["email"]
    assert payload["user"]["role"] == "CITIZEN"


def test_register_then_login_succeeds_with_unicode_name(client):
    register_payload = {
        "name": "சந்தா குமார்",
        "email": "fresh.unicode@example.com",
        "phone": "9876500888",
        "password": "FreshPass123",
        "date_of_birth": "1993-02-11",
        "gender": "Male",
    }
    register_response = client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    payload = login_response.get_json()
    assert payload["token"]
    assert payload["user"]["name"] == register_payload["name"]


def test_password_reset_flow(client, app, monkeypatch):
    with app.app_context():
        user = create_user("Citizen One", "citizen1@example.com", "9876500001")
        user_id = user.id
        user_email = user.email

    monkeypatch.setattr(OTPService, "generate_otp", staticmethod(lambda: 123456))

    forgot_resp = client.post("/api/auth/forgot-password", json={"email": user_email})
    assert forgot_resp.status_code == 200

    verify_resp = client.post(
        "/api/auth/verify-reset-otp",
        json={"email": user_email, "otp": "123456"},
    )
    assert verify_resp.status_code == 200
    reset_token = verify_resp.get_json()["reset_token"]
    token_payload = decode_token(reset_token, expected_type="password_reset")
    assert token_payload["user_id"] == user_id
    assert token_payload["token_type"] == "password_reset"

    reset_resp = client.post(
        "/api/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "NewPassword123"},
    )
    assert reset_resp.status_code == 200

    with app.app_context():
        updated_user = User.query.get(user_id)
        assert updated_user.check_password("NewPassword123")

    access_token = create_access_token(user_id)
    invalid_resp = client.post(
        "/api/auth/reset-password",
        json={"reset_token": access_token, "new_password": "AnotherPass123"},
    )
    assert invalid_resp.status_code == 401


def test_add_comment_as_citizen_persists_comment_and_notification(client, app):
    with app.app_context():
        citizen = create_user("Citizen Two", "citizen2@example.com", "9876500002")
        officer = create_user(
            "Officer One",
            "officer1@example.com",
            "9876500003",
            role="OFFICER",
            department="Water Supply",
        )
        grievance = create_grievance(
            user_id=citizen.id,
            department="Water Supply",
            status="Assigned to Department",
            assigned_officer_id=officer.id,
        )
        citizen_id = citizen.id
        grievance_id = grievance.id
        officer_id = officer.id

    response = client.post(
        f"/api/grievances/{grievance_id}/comments",
        json={"comment_text": "Please prioritize this issue; there is no water supply."},
        headers=auth_headers(citizen_id),
    )
    assert response.status_code == 201

    with app.app_context():
        saved_comment = GrievanceComment.query.filter_by(
            grievance_id=grievance_id,
            user_id=citizen_id,
        ).first()
        assert saved_comment is not None
        assert saved_comment.notified_officer_id == officer_id
        assert saved_comment.notification_sent_at is not None
        assert saved_comment.response_deadline is not None

        saved_notification = Notification.query.filter_by(
            user_id=officer_id,
            related_grievance_id=grievance_id,
            notification_type="comment",
        ).first()
        assert saved_notification is not None


def test_add_comment_as_officer_persists_comment(client, app):
    with app.app_context():
        citizen = create_user("Citizen Three", "citizen3@example.com", "9876500004")
        officer = create_user(
            "Officer Two",
            "officer2@example.com",
            "9876500005",
            role="OFFICER",
            department="Roads and Public Works",
        )
        grievance = create_grievance(
            user_id=citizen.id,
            department="Roads and Public Works",
            status="Assigned to Department",
            assigned_officer_id=officer.id,
        )
        officer_id = officer.id
        grievance_id = grievance.id

    response = client.post(
        f"/api/grievances/{grievance_id}/comments",
        json={"comment_text": "Site inspection completed. Work order has been raised."},
        headers=auth_headers(officer_id),
    )
    assert response.status_code == 201

    with app.app_context():
        saved_comment = GrievanceComment.query.filter_by(
            grievance_id=grievance_id,
            user_id=officer_id,
        ).first()
        assert saved_comment is not None
        assert saved_comment.user_role == "OFFICER"


def test_assign_officer_uses_previous_status_in_notification(client, app, monkeypatch):
    with app.app_context():
        admin = create_user("Admin One", "admin1@example.com", "9876500006", role="ADMIN")
        citizen = create_user("Citizen Four", "citizen4@example.com", "9876500007")
        officer = create_user(
            "Officer Three",
            "officer3@example.com",
            "9876500008",
            role="OFFICER",
            department="Sanitation and Waste Management",
        )
        grievance = create_grievance(
            user_id=citizen.id,
            department="Sanitation and Waste Management",
            status="Under Progress",
        )
        admin_id = admin.id
        officer_id = officer.id
        grievance_id = grievance.id

    captured_payload = {}

    def capture_status_email(**kwargs):
        captured_payload.update(kwargs)
        return True

    monkeypatch.setattr(
        EmailService,
        "send_status_update_notification",
        staticmethod(capture_status_email),
    )

    response = client.post(
        "/api/admin/assign-officer",
        json={"grievance_id": grievance_id, "officer_id": officer_id},
        headers=auth_headers(admin_id),
    )
    assert response.status_code == 200
    assert captured_payload["old_status"] == "Under Progress"
    assert captured_payload["new_status"] == "Assigned to Department"

    with app.app_context():
        grievance = Grievance.query.get(grievance_id)
        assert grievance.assigned_officer_id == officer_id
        assert grievance.status == "Assigned to Department"


def test_grievance_status_update_preserves_old_status_for_notification(client, app, monkeypatch):
    with app.app_context():
        citizen = create_user("Citizen Five", "citizen5@example.com", "9876500009")
        officer = create_user(
            "Officer Four",
            "officer4@example.com",
            "9876500010",
            role="OFFICER",
            department="Electricity",
        )
        grievance = create_grievance(
            user_id=citizen.id,
            department="Electricity",
            status="Assigned to Department",
            assigned_officer_id=officer.id,
        )
        officer_id = officer.id
        grievance_id = grievance.id

    captured_payload = {}

    def capture_status_email(**kwargs):
        captured_payload.update(kwargs)
        return True

    monkeypatch.setattr(
        EmailService,
        "send_status_update_notification",
        staticmethod(capture_status_email),
    )

    response = client.post(
        f"/api/grievances/{grievance_id}/update",
        json={"status": "Under Progress", "message": "Technician assigned and work started."},
        headers=auth_headers(officer_id),
    )
    assert response.status_code == 200
    assert captured_payload["old_status"] == "Assigned to Department"
    assert captured_payload["new_status"] == "Under Progress"

    with app.app_context():
        grievance = Grievance.query.get(grievance_id)
        assert grievance.status == "Under Progress"
        status_update = GrievanceUpdate.query.filter_by(
            grievance_id=grievance_id,
            status="Under Progress",
        ).first()
        assert status_update is not None


def test_send_otp_response_omits_demo_metadata(client, monkeypatch):
    monkeypatch.setattr(OTPService, "generate_otp", staticmethod(lambda: 654321))

    response = client.post(
        "/api/auth/send-otp",
        json={"identifier": "otp.citizen@example.com", "channel": "email"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["message"] == "OTP sent to otp.citizen@example.com via email"
    assert "demo_mode" not in payload
    assert "demo_note" not in payload


def test_phone_otp_requires_explicit_demo_sms_mode(client):
    original_sms_mode = Config.DEMO_SMS_MODE
    Config.DEMO_SMS_MODE = False

    try:
        response = client.post(
            "/api/auth/send-otp",
            json={"identifier": "9876500999", "channel": "phone"},
        )
    finally:
        Config.DEMO_SMS_MODE = original_sms_mode

    assert response.status_code == 400
    assert "not configured" in response.get_json()["error"].lower()

