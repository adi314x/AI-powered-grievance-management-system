#!/usr/bin/env python3
"""End-to-end local smoke test harness for critical backend flows.

This script bootstraps an isolated SQLite database, runs migrations + seed,
and executes a strict pass/fail smoke suite against Flask test client routes.

Usage:
    python scripts/smoke_test.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CITIZEN_EMAIL = "citizen@example.com"
CITIZEN_OLD_PASSWORD = "citizen123"
CITIZEN_NEW_PASSWORD = "CitizenNew123"
ADMIN_EMAIL = "admin@grievance.gov"
ADMIN_PASSWORD = "admin123"
OFFICER_PASSWORD = "officer123"

PNG_1X1 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAgMBgJ0N8iQAAAAASUVORK5CYII="
)


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str


class SmokeFailure(AssertionError):
    pass


class SmokeRunner:
    def __init__(self):
        self.results: list[StepResult] = []
        self.state = {
            "citizen_token": None,
            "admin_token": None,
            "officer_token": None,
            "officer_email": None,
            "grievance_id": None,
            "fraud_report_id": None,
        }

        from backend.app import create_app

        self.app = create_app()
        self.client = self.app.test_client()

    def add_result(self, name: str, ok: bool, detail: str) -> None:
        self.results.append(StepResult(name=name, ok=ok, detail=detail))
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name} :: {detail}")

    @staticmethod
    def expect(condition: bool, message: str) -> None:
        if not condition:
            raise SmokeFailure(message)

    def api(self, method: str, path: str, token: str | None = None, payload: dict | None = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.client.open(path, method=method, headers=headers, json=payload)
        data = response.get_json(silent=True)
        return response, data

    def run_step(self, name: str, fn: Callable[[], None]) -> None:
        try:
            fn()
            self.add_result(name, True, "ok")
        except Exception as exc:  # noqa: BLE001
            self.add_result(name, False, str(exc))

    def run(self) -> int:
        from backend.extensions import db
        from backend.models import Grievance, User
        from backend.services.otp_service import OTPService

        captured = {"otp": None}
        original_create_otp = OTPService.create_otp_request

        def wrapped_create_otp(identifier, channel):
            otp, error = original_create_otp(identifier, channel)
            if identifier == CITIZEN_EMAIL and otp:
                captured["otp"] = str(otp)
            return otp, error

        OTPService.create_otp_request = staticmethod(wrapped_create_otp)

        def health_check():
            response, data = self.api("GET", "/health")
            self.expect(response.status_code == 200, f"status={response.status_code}")
            self.expect((data or {}).get("database", {}).get("connected") is True, "database not connected")

        def citizen_login_old_password():
            response, data = self.api(
                "POST",
                "/api/auth/login",
                payload={"email": CITIZEN_EMAIL, "password": CITIZEN_OLD_PASSWORD},
            )
            self.expect(response.status_code == 200, f"status={response.status_code}, payload={data}")
            token = (data or {}).get("token")
            self.expect(bool(token), "missing citizen token")
            self.state["citizen_token"] = token

        def current_user():
            response, data = self.api("GET", "/api/auth/me", token=self.state["citizen_token"])
            self.expect(response.status_code == 200, f"status={response.status_code}, payload={data}")
            self.expect((data or {}).get("user", {}).get("email") == CITIZEN_EMAIL, "unexpected /me email")

        def password_reset_flow():
            response, data = self.api(
                "POST",
                "/api/auth/forgot-password",
                payload={"email": CITIZEN_EMAIL},
            )
            self.expect(response.status_code == 200, f"forgot status={response.status_code}, payload={data}")
            self.expect(bool(captured["otp"]), "OTP was not captured")

            response, data = self.api(
                "POST",
                "/api/auth/verify-reset-otp",
                payload={"email": CITIZEN_EMAIL, "otp": captured["otp"]},
            )
            self.expect(response.status_code == 200, f"verify status={response.status_code}, payload={data}")
            reset_token = (data or {}).get("reset_token")
            self.expect(bool(reset_token), "missing reset token")

            response, data = self.api(
                "POST",
                "/api/auth/reset-password",
                payload={"reset_token": reset_token, "new_password": CITIZEN_NEW_PASSWORD},
            )
            self.expect(response.status_code == 200, f"reset status={response.status_code}, payload={data}")

            response, data = self.api(
                "POST",
                "/api/auth/login",
                payload={"email": CITIZEN_EMAIL, "password": CITIZEN_NEW_PASSWORD},
            )
            self.expect(response.status_code == 200, f"new login status={response.status_code}, payload={data}")
            token = (data or {}).get("token")
            self.expect(bool(token), "missing token after password reset")
            self.state["citizen_token"] = token

        def submit_grievance():
            complaint = (
                "There is a dangerous pothole and damaged road surface near the main bus stand, "
                "causing repeated accidents during peak traffic hours."
            )
            location = "Near Central Bus Stand, Anna Salai, Chennai"

            response, data = self.api(
                "POST",
                "/api/grievances/predict-department",
                token=self.state["citizen_token"],
                payload={"complaint_text": complaint},
            )
            self.expect(response.status_code == 200, f"predict status={response.status_code}, payload={data}")
            images_required = bool((data or {}).get("images_required"))

            if images_required:
                response_noimg, data_noimg = self.api(
                    "POST",
                    "/api/grievances/submit",
                    token=self.state["citizen_token"],
                    payload={"complaint_text": complaint, "location": location, "images": []},
                )
                self.expect(
                    response_noimg.status_code == 400,
                    f"expected 400 without image, got {response_noimg.status_code}, payload={data_noimg}",
                )

            response, data = self.api(
                "POST",
                "/api/grievances/submit",
                token=self.state["citizen_token"],
                payload={"complaint_text": complaint, "location": location, "images": [PNG_1X1]},
            )
            self.expect(response.status_code == 201, f"submit status={response.status_code}, payload={data}")
            grievance_id = (data or {}).get("grievance_id")
            self.expect(bool(grievance_id), "missing grievance_id")
            self.state["grievance_id"] = grievance_id

        def admin_login():
            response, data = self.api(
                "POST",
                "/api/auth/login",
                payload={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            )
            self.expect(response.status_code == 200, f"admin login status={response.status_code}, payload={data}")
            token = (data or {}).get("token")
            self.expect(bool(token), "missing admin token")
            self.state["admin_token"] = token

        def assign_officer_flow():
            grievance_id = self.state["grievance_id"]
            with self.app.app_context():
                grievance = db.session.get(Grievance, grievance_id)
                self.expect(grievance is not None, "grievance not found in DB")

                grievance.requires_manual_triage = False
                grievance.triage_reason = None
                if grievance.assigned_department == "Manual Review Queue":
                    grievance.assigned_department = grievance.predicted_department
                if grievance.status == "Manual Review Required":
                    grievance.status = "Received"
                db.session.commit()

                mismatch = (
                    User.query.filter(User.role == "OFFICER", User.department != grievance.assigned_department)
                    .order_by(User.id.asc())
                    .first()
                )
                match = (
                    User.query.filter(User.role == "OFFICER", User.department == grievance.assigned_department)
                    .order_by(User.id.asc())
                    .first()
                )
                self.expect(mismatch is not None, "no mismatch officer")
                self.expect(match is not None, f"no matching officer for {grievance.assigned_department}")
                self.state["officer_email"] = match.email
                mismatch_id = mismatch.id
                match_id = match.id

            response, data = self.api(
                "POST",
                "/api/admin/assign-officer",
                token=self.state["admin_token"],
                payload={"grievance_id": grievance_id, "officer_id": mismatch_id},
            )
            self.expect(response.status_code == 400, f"expected mismatch 400, got {response.status_code}, payload={data}")

            response, data = self.api(
                "POST",
                "/api/admin/assign-officer",
                token=self.state["admin_token"],
                payload={"grievance_id": grievance_id, "officer_id": match_id},
            )
            self.expect(response.status_code == 200, f"match assign status={response.status_code}, payload={data}")

        def officer_login():
            response, data = self.api(
                "POST",
                "/api/auth/login",
                payload={"email": self.state["officer_email"], "password": OFFICER_PASSWORD},
            )
            self.expect(response.status_code == 200, f"officer login status={response.status_code}, payload={data}")
            token = (data or {}).get("token")
            self.expect(bool(token), "missing officer token")
            self.state["officer_token"] = token

        def officer_citizen_comment_flow():
            grievance_id = self.state["grievance_id"]

            response, data = self.api(
                "POST",
                f"/api/grievances/{grievance_id}/update",
                token=self.state["officer_token"],
                payload={"status": "Under Progress", "message": "Site inspection completed. Repair team scheduled."},
            )
            self.expect(response.status_code == 200, f"update status={response.status_code}, payload={data}")

            response, data = self.api(
                "POST",
                f"/api/grievances/{grievance_id}/comments",
                token=self.state["officer_token"],
                payload={"comment_text": "Repair crew has been scheduled and work starts tomorrow."},
            )
            self.expect(response.status_code == 201, f"officer comment status={response.status_code}, payload={data}")

            response, data = self.api(
                "POST",
                f"/api/grievances/{grievance_id}/comments",
                token=self.state["citizen_token"],
                payload={"comment_text": "Please complete this soon because accidents are increasing."},
            )
            self.expect(response.status_code == 201, f"citizen comment status={response.status_code}, payload={data}")

        def fraud_and_admin_action_flow():
            grievance_id = self.state["grievance_id"]

            response, data = self.api(
                "POST",
                f"/api/grievances/{grievance_id}/report-fraud",
                token=self.state["officer_token"],
                payload={
                    "fraud_type": "duplicate",
                    "description": "Potential duplicate complaint detected after field verification.",
                    "site_visit_notes": "Duplicate marker observed at same location.",
                    "evidence": "photo-set-1",
                },
            )
            self.expect(response.status_code == 201, f"fraud report status={response.status_code}, payload={data}")
            report_id = (data or {}).get("fraud_report_id")
            self.expect(bool(report_id), "missing fraud_report_id")
            self.state["fraud_report_id"] = report_id

            response, data = self.api("GET", "/api/grievances/fraud-reports", token=self.state["admin_token"])
            self.expect(response.status_code == 200, f"fraud list status={response.status_code}, payload={data}")

            response, data = self.api(
                "POST",
                f"/api/grievances/fraud-reports/{report_id}/action",
                token=self.state["admin_token"],
                payload={"action": "dismiss", "admin_notes": "Verified as genuine complaint."},
            )
            self.expect(response.status_code == 200, f"fraud action status={response.status_code}, payload={data}")

        def model_and_public_feeds():
            grievance_id = self.state["grievance_id"]

            response, data = self.api(
                "POST",
                f"/api/grievances/{grievance_id}/update",
                token=self.state["officer_token"],
                payload={"status": "Resolved", "message": "Repair completed and issue closed."},
            )
            self.expect(response.status_code == 200, f"resolve status={response.status_code}, payload={data}")

            response, data = self.api("GET", "/api/admin/model-status", token=self.state["admin_token"])
            self.expect(response.status_code == 200, f"model-status={response.status_code}, payload={data}")
            self.expect("quality_assessment" in (data or {}), "missing quality_assessment")

            response, data = self.api("GET", "/api/public/stats")
            self.expect(response.status_code == 200, f"public stats status={response.status_code}, payload={data}")
            self.expect("total_grievances" in (data or {}), "missing total_grievances")

            response, data = self.api("GET", "/api/public/resolved-cases?limit=6")
            self.expect(response.status_code == 200, f"resolved-cases status={response.status_code}, payload={data}")
            self.expect((data or {}).get("count", 0) >= 1, "resolved feed missing expected case")

        try:
            self.run_step("Health endpoint", health_check)
            self.run_step("Citizen login", citizen_login_old_password)
            self.run_step("/api/auth/me", current_user)
            self.run_step("Forgot -> verify reset OTP -> reset password -> login", password_reset_flow)
            self.run_step("Predict department + submit grievance", submit_grievance)
            self.run_step("Admin login", admin_login)
            self.run_step("Assign officer mismatch reject + match success", assign_officer_flow)
            self.run_step("Assigned officer login", officer_login)
            self.run_step("Officer status/comment + citizen comment", officer_citizen_comment_flow)
            self.run_step("Fraud report + admin action", fraud_and_admin_action_flow)
            self.run_step("Model status + public stats/resolved-cases", model_and_public_feeds)
        finally:
            OTPService.create_otp_request = original_create_otp

        passed = sum(1 for item in self.results if item.ok)
        failed = sum(1 for item in self.results if not item.ok)

        print("\n=== Smoke Test Summary ===")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if failed:
            print("\nFailed checks:")
            for item in self.results:
                if not item.ok:
                    print(f"- {item.name}: {item.detail}")
            return 1

        return 0


def run_command(cmd: list[str], env: dict[str, str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def build_runtime_env(db_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(REPO_ROOT),
            "FLASK_ENV": "development",
            "SECRET_KEY": "smoke-secret",
            "APP_BASE_URL": "http://localhost:8000",
            "DATABASE_URL": f"sqlite:///{db_path}",
            "DEMO_EMAIL_MODE": "true",
            "DEMO_SMS_MODE": "true",
            "AUTO_CREATE_TABLES": "false",
            "ENABLE_SCHEDULER": "false",
            "ENABLE_STARTUP_MODEL_LOAD": "true",
        }
    )
    return env


def run_smoke_suite(db_path: Path) -> int:
    runtime_env = build_runtime_env(db_path)

    # Keep the current process env in sync with subprocess bootstrap env.
    os.environ.update(runtime_env)

    run_command([sys.executable, "-m", "flask", "--app", "backend.app:create_app", "db", "upgrade"], runtime_env)
    run_command([sys.executable, "manage.py", "seed"], runtime_env)

    runner = SmokeRunner()
    return runner.run()


def main() -> int:
    print("== Smart Grievance System Smoke Test ==")
    with tempfile.TemporaryDirectory(prefix="sgs_smoke_") as temp_dir:
        db_path = Path(temp_dir) / "smoke_test.db"
        print(f"Using isolated DB: {db_path}")
        return run_smoke_suite(db_path)


if __name__ == "__main__":
    raise SystemExit(main())
