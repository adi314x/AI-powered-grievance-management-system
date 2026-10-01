from datetime import datetime, timedelta

from backend.extensions import db
from backend.models import Grievance, User


def create_user(name, email, phone, role="CITIZEN", password="Password123"):
    user = User(
        name=name,
        email=email,
        phone=phone,
        role=role,
        email_verified=True,
        phone_verified=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def create_grievance(user_id, department, status, location, complaint_text, updated_at):
    grievance = Grievance(
        user_id=user_id,
        complaint_text=complaint_text,
        predicted_department=department,
        assigned_department=department,
        status=status,
        location=location,
        created_at=updated_at - timedelta(days=2),
        updated_at=updated_at,
    )
    db.session.add(grievance)
    db.session.commit()
    return grievance


def test_public_resolved_cases_returns_only_resolved_and_closed(client, app):
    with app.app_context():
        citizen = create_user("Citizen One", "phase5-citizen@example.com", "9988776655")
        create_grievance(
            citizen.id,
            "Water Supply",
            "Resolved",
            "Block A, Anna Nagar, Chennai, Tamil Nadu",
            "Water pipeline leak repaired and pressure restored.",
            datetime.utcnow() - timedelta(hours=3),
        )
        create_grievance(
            citizen.id,
            "Roads and Public Works",
            "Closed",
            "Ward 9, Pune, Maharashtra",
            "Pothole near market filled and road patch completed.",
            datetime.utcnow() - timedelta(days=1),
        )
        create_grievance(
            citizen.id,
            "Electricity",
            "Under Progress",
            "Sector 12, Noida, Uttar Pradesh",
            "Intermittent power outage still under inspection.",
            datetime.utcnow(),
        )

    response = client.get("/api/public/resolved-cases?limit=10")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["count"] == 2
    statuses = {case["status"] for case in payload["cases"]}
    assert statuses == {"Resolved", "Closed"}


def test_public_resolved_cases_anonymizes_location_and_clamps_limit(client, app):
    with app.app_context():
        citizen = create_user("Citizen Two", "phase5-citizen2@example.com", "9988776644")
        for idx in range(15):
            create_grievance(
                citizen.id,
                "Sanitation and Waste Management",
                "Resolved",
                f"Lat: 12.{idx:02d}, Long: 80.{idx:02d} (GPS coordinates)",
                f"Resolved health-related complaint number {idx} after field verification.",
                datetime.utcnow() - timedelta(hours=idx),
            )

    response = client.get("/api/public/resolved-cases?limit=99")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["count"] == 12
    assert len(payload["cases"]) == 12
    assert all(case["location"] == "GPS area" for case in payload["cases"])
    assert all("complaint number" in case["description"] for case in payload["cases"])

