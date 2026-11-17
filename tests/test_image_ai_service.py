"""Tests for the ONNX-backed grievance image analysis service."""

import base64
import io
import json

from PIL import Image

from backend.extensions import db
from backend.models import Grievance, Notification, User
from backend.routes.auth import create_access_token
from backend.services.image_ai_service import (
    ISSUE_DEPARTMENT_MAP,
    ImageAIService,
    image_ai_service,
)


def _data_url(color=(120, 140, 100), size=(64, 64)):
    image = Image.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    payload = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


def test_vision_models_load_and_return_expected_fields():
    result = image_ai_service.analyze_base64_image(_data_url())

    assert result["available"] is True, result.get("reason")
    assert result["issue_type"] in {"garbage", "other", "pothole"}
    assert 0.0 <= result["issue_confidence"] <= 1.0
    assert 0.0 <= result["ai_confidence"] <= 1.0
    assert set(result["ai_scores"]) == {"fake", "real"}
    assert result["ai_label"] in {"fake", "real"}


def test_analyze_images_aggregates_and_keeps_per_image_results():
    result = image_ai_service.analyze_images(
        [_data_url(), _data_url(color=(10, 20, 30))]
    )

    assert result["available"] is True
    assert result["images_requested"] == 2
    assert result["images_analyzed"] == 2
    assert len(result["per_image"]) == 2
    assert result["issue_type"] in {"garbage", "other", "pothole"}
    assert result["ai_label"] in {"fake", "real"}
    assert isinstance(result["recommendation"], str)


def test_analyze_images_handles_empty_and_invalid_input():
    empty = image_ai_service.analyze_images([])
    assert empty["available"] is False

    invalid = image_ai_service.analyze_images(["not-an-image"])
    assert invalid["available"] is False
    assert "reason" in invalid


def test_missing_model_directory_is_graceful(tmp_path):
    service = ImageAIService(model_dir=str(tmp_path))
    result = service.analyze_base64_image(_data_url())

    assert result["available"] is False
    assert "Missing vision model" in result["reason"]


def test_issue_department_mapping():
    assert ISSUE_DEPARTMENT_MAP["pothole"] == "Roads and Public Works"
    assert ISSUE_DEPARTMENT_MAP["garbage"] == "Sanitation and Waste Management"
    assert ISSUE_DEPARTMENT_MAP["water_leak"] == "Water Supply"


def test_submit_persists_vision_analysis_and_flags_ai_image(client, app, monkeypatch):
    with app.app_context():
        citizen = User(
            name="Vision Citizen",
            email="vision-citizen@example.com",
            phone="9900000091",
            role="CITIZEN",
            email_verified=True,
            phone_verified=True,
        )
        citizen.set_password("Password123")
        admin = User(
            name="Vision Admin",
            email="vision-admin@example.com",
            phone="9900000092",
            role="ADMIN",
            email_verified=True,
            phone_verified=True,
        )
        admin.set_password("Password123")
        db.session.add_all([citizen, admin])
        db.session.commit()
        citizen_id = citizen.id
        admin_id = admin.id

    fake_analysis = {
        "available": True,
        "model_version": "test-v1",
        "images_requested": 1,
        "images_analyzed": 1,
        "issue_type": "pothole",
        "issue_display": "Pothole / road damage",
        "issue_confidence": 0.91,
        "issue_confidence_pct": 91.0,
        "issue_scores": {"pothole": 0.91, "garbage": 0.05, "other": 0.04},
        "issue_department": "Roads and Public Works",
        "ai_label": "fake",
        "ai_generated": True,
        "ai_confidence": 0.93,
        "ai_confidence_pct": 93.0,
        "ai_scores": {"fake": 0.93, "real": 0.07},
        "recommendation": "Verify this image manually.",
    }

    monkeypatch.setattr(
        "backend.routes.grievances.image_ai_service.analyze_images",
        lambda images: dict(fake_analysis),
    )
    monkeypatch.setattr(
        "backend.routes.grievances.classifier.predict_with_confidence",
        lambda *args, **kwargs: {
            "department": "Roads and Public Works",
            "confidence": 0.92,
            "source": "mock",
            "model_loaded": True,
        },
    )
    monkeypatch.setattr(
        "backend.routes.grievances.ContentModerator.moderate_content",
        lambda *args, **kwargs: {
            "is_safe": True,
            "score": 0,
            "severity": None,
            "flags": [],
        },
    )

    response = client.post(
        "/api/grievances/submit",
        json={
            "complaint_text": "There is a large pothole on the main road near the school.",
            "location": "Main road near the school, Ward 4",
            "images": [_data_url()],
        },
        headers={"Authorization": f"Bearer {create_access_token(citizen_id)}"},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["image_analysis"]["issue_type"] == "pothole"

    with app.app_context():
        grievance = Grievance.query.get(payload["grievance_id"])
        assert grievance.ai_image_detected is True
        assert grievance.ai_detection_confidence == 93.0
        assert grievance.is_flagged is True

        details = json.loads(grievance.ai_detection_details)
        assert details["issue_type"] == "pothole"
        assert details["text_department"] == "Roads and Public Works"
        assert details["department_match"] is True

        notification = Notification.query.filter_by(
            user_id=admin_id,
            related_grievance_id=grievance.id,
            notification_type="ai_image_review",
        ).first()
        assert notification is not None
