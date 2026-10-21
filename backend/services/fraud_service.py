from datetime import datetime

from backend.extensions import db
from backend.models import GrievanceUpdate, User
from backend.services.email_service import EmailService
from backend.services.notification_service import NotificationService
from backend.utils.roles import ADMIN_ROLE_VALUES


def review_fraud_report(report, admin_user, action, admin_notes="", suspend_user=False):
    grievance = report.grievance
    citizen = grievance.user
    now = datetime.utcnow()

    report.admin_notes = admin_notes
    report.reviewed_at = now

    if action == "dismiss":
        report.status = "Dismissed"
        report.action_taken = "Dismissed"
        grievance.status = "Assigned to Department"
        update_message = f"Fraud report dismissed by Admin. Resuming investigations. Notes: {admin_notes}"
        if citizen:
            NotificationService.queue_notification(
                user_id=citizen.id,
                title=f"Fraud Report Dismissed - Grievance #{grievance.id}",
                message="The fraud report on your grievance was dismissed.",
                notification_type="fraud_review",
                related_grievance_id=grievance.id,
            )
    else:
        report.status = "Verified"
        grievance.status = "Closed"
        update_message = f"Fraud verified by Admin. Grievance closed. Notes: {admin_notes}"
        if citizen:
            citizen.fraud_warnings = (citizen.fraud_warnings or 0) + 1
            report.action_taken = "Warning"
            NotificationService.queue_notification(
                user_id=citizen.id,
                title=f"Fraud Warning - Grievance #{grievance.id}",
                message=f"A fraud report was verified. Warning count: {citizen.fraud_warnings}.",
                notification_type="fraud_warning",
                related_grievance_id=grievance.id,
            )

            if suspend_user or action == "suspend":
                citizen.account_suspended = True
                citizen.suspension_reason = (
                    f"Verified fraud on Grievance #{grievance.id}: {admin_notes}"
                )
                report.action_taken = "Account_Suspended"
                NotificationService.queue_notification(
                    user_id=citizen.id,
                    title="Account Suspended",
                    message=citizen.suspension_reason,
                    notification_type="account_suspended",
                    related_grievance_id=grievance.id,
                )

    db.session.add(GrievanceUpdate(
        grievance_id=grievance.id,
        status=grievance.status,
        message=update_message,
        updated_by_role="ADMIN",
        updated_by_name=admin_user.name,
    ))
    db.session.commit()

    if citizen and action == "dismiss":
        EmailService.send_fraud_review_notice(
            citizen_email=citizen.email,
            citizen_name=citizen.name,
            grievance_id=grievance.id,
            stage="dismissed",
            details=admin_notes,
        )
    elif citizen:
        if suspend_user or action == "suspend":
            EmailService.send_account_suspension_email(
                citizen_email=citizen.email,
                citizen_name=citizen.name,
                reason=citizen.suspension_reason,
                grievance_id=grievance.id,
            )
        else:
            EmailService.send_account_warning_email(
                citizen_email=citizen.email,
                citizen_name=citizen.name,
                grievance_id=grievance.id,
                warning_count=citizen.fraud_warnings,
                reason=admin_notes,
            )

    return grievance


def notify_fraud_report(report, officer):
    grievance = report.grievance
    citizen = grievance.user
    admins = User.query.filter(User.role.in_(ADMIN_ROLE_VALUES)).all()

    for admin in admins:
        NotificationService.queue_notification(
            user_id=admin.id,
            title=f"Fraud Report Requires Review - Grievance #{grievance.id}",
            message=f"{officer.name} reported suspected fraud ({report.fraud_type}).",
            notification_type="fraud_report",
            related_grievance_id=grievance.id,
        )

    if citizen:
        NotificationService.queue_notification(
            user_id=citizen.id,
            title=f"Grievance #{grievance.id} Under Review",
            message="Your grievance has been sent for fraud review.",
            notification_type="fraud_warning",
            related_grievance_id=grievance.id,
        )

    db.session.commit()

    for admin in admins:
        EmailService.send_fraud_report_alert(
            admin_email=admin.email,
            admin_name=admin.name,
            grievance_id=grievance.id,
            officer_name=officer.name,
            fraud_type=report.fraud_type,
            description=report.description,
        )

    if citizen:
        EmailService.send_fraud_review_notice(
            citizen_email=citizen.email,
            citizen_name=citizen.name,
            grievance_id=grievance.id,
            stage="under_review",
            details=report.description,
        )
