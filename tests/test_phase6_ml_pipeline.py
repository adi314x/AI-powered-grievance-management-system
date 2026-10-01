import pytest
from backend.config import Config
from backend.extensions import db
from backend.models import Grievance, GrievanceUpdate, Notification, User
from backend.models_addons import DepartmentCorrectionLog
from backend.routes.auth import create_access_token
from backend.services import model_retrain
from backend.services.classifier import classifier

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

def test_predict_department_returns_confidence_and_routing(client, app, monkeypatch):
    with app.app_context():
        citizen = create_user("Citizen One", "phase6-citizen1@example.com", "9876520001")
        citizen_id = citizen.id

    monkeypatch.setattr(
        "backend.routes.grievances.classifier.predict_with_confidence",
        lambda text: {
            "department": "Water Supply",
            "confidence": 0.88,
            "model_loaded": True,
            "source": "ml",
            "top_candidates": [
                {"department": "Water Supply", "confidence": 0.88},
                {"department": "Sanitation and Waste Management", "confidence": 0.09},
            ],
        },
    )

    response = client.post(
        "/api/grievances/predict-department",
        json={"complaint_text": "Water leakage continues near the main road and needs urgent repair."},
        headers=auth_headers(citizen_id),
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["department"] == "Water Supply"
    assert payload["routing_decision"] == "auto_assign"

def test_submit_low_confidence_routes_to_manual_review(client, app, monkeypatch):
    with app.app_context():
        citizen = create_user("Citizen Two", "phase6-citizen2@example.com", "9876520002")
        admin = create_user("Admin One", "phase6-admin1@example.com", "9876520003", role="ADMIN")
        citizen_id = citizen.id
        admin_id = admin.id

    monkeypatch.setattr(
        "backend.routes.grievances.classifier.predict_with_confidence",
        lambda text: {
            "department": "Education",
            "confidence": 0.22,
            "model_loaded": True,
            "source": "ml",
            "top_candidates": [{"department": "Education", "confidence": 0.22}],
        },
    )

    response = client.post(
        "/api/grievances/submit",
        json={
            "complaint_text": "There are repeated unauthorized activities in my neighborhood, please verify quickly for manual review test",
            "location": "Near market signal, Ward 4, Old Town",
            "images": [],
        },
        headers=auth_headers(citizen_id),
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["routing_decision"] == "manual_review"
    grievance_id = payload["grievance_id"]

    with app.app_context():
        grievance = Grievance.query.get(grievance_id)
        assert grievance.status == "Manual Review Required"
        assert grievance.requires_manual_triage is True

def test_manual_triage_assignment_logs_department_correction(client, app):
    with app.app_context():
        admin = create_user("Admin Two", "phase6-admin2@example.com", "9876520005", role="ADMIN")
        citizen = create_user("Citizen Four", "phase6-citizen4@example.com", "9876520006")
        officer = create_user(
            "Officer One",
            "phase6-officer1@example.com",
            "9876520007",
            role="OFFICER",
            department="Electricity",
        )

        grievance = Grievance(
            user_id=citizen.id,
            complaint_text="Power outages continue every night in our sector.",
            predicted_department="Water Supply",
            assigned_department=Config.ML_MANUAL_REVIEW_DEPARTMENT,
            prediction_confidence=0.31,
            prediction_source="ml",
            requires_manual_triage=True,
            status="Manual Review Required",
            location="Ward 10 near bus stand",
        )
        db.session.add(grievance)
        db.session.commit()

        admin_id = admin.id
        officer_id = officer.id
        grievance_id = grievance.id

    response = client.post(
        "/api/admin/assign-officer",
        json={"grievance_id": grievance_id, "officer_id": officer_id},
        headers=auth_headers(admin_id),
    )
    assert response.status_code == 200

    with app.app_context():
        grievance = db.session.get(Grievance, grievance_id)
        assert grievance.assigned_department == "Electricity"
        
        correction = DepartmentCorrectionLog.query.filter_by(grievance_id=grievance_id).first()
        assert correction is not None
        assert correction.predicted_department == "Water Supply"
        assert correction.corrected_department == "Electricity"

