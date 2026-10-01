"""
Comment Escalation Service
Handles automatic escalation of citizen comments when officers don't respond in time.
"""
from datetime import datetime

from backend.extensions import db
from backend.models import EscalationLog, Grievance, GrievanceComment, User
from backend.services.email_service import EmailService
from backend.services.notification_service import NotificationService
from backend.utils.roles import ADMIN_ROLE_VALUES, OFFICER_ROLE_VALUES, is_role, role_level_for_log


def _format_timestamp(value):
    return value.strftime('%Y-%m-%d %H:%M') if value else 'N/A'


def get_escalation_recipient(current_officer, grievance):
    """
    Resolve escalation target using active workflow:
    1. Assigned officer (if different from currently notified officer)
    2. Another officer in same department
    3. Admin fallback
    """
    if not current_officer:
        return None

    if grievance.assigned_officer_id and grievance.assigned_officer_id != current_officer.id:
        assigned_officer = User.query.get(grievance.assigned_officer_id)
        if (
            assigned_officer
            and is_role(assigned_officer, 'OFFICER')
            and assigned_officer.department == grievance.assigned_department
        ):
            return assigned_officer

    department_officer = User.query.filter(
        User.role.in_(OFFICER_ROLE_VALUES),
        User.department == grievance.assigned_department,
        User.id != current_officer.id,
    ).order_by(User.created_at.asc(), User.id.asc()).first()
    if department_officer:
        return department_officer

    return User.query.filter(User.role.in_(ADMIN_ROLE_VALUES)).order_by(User.created_at.asc(), User.id.asc()).first()


def _create_escalation_log(grievance_id, from_officer, to_officer, reason, escalation_type):
    if not to_officer:
        return
    log = EscalationLog(
        grievance_id=grievance_id,
        from_officer_id=from_officer.id if from_officer else None,
        to_officer_id=to_officer.id,
        from_role_level=role_level_for_log(from_officer) if from_officer else 0,
        to_role_level=role_level_for_log(to_officer),
        reason=reason,
        escalation_type=escalation_type,
    )
    db.session.add(log)


def _send_pending_emails(pending_email_jobs):
    for email_fn, kwargs in pending_email_jobs:
        try:
            email_fn(**kwargs)
        except Exception as email_error:
            print(f"Failed to send escalation email: {email_error}")


def check_and_escalate_comments(now=None):
    """
    Escalate overdue citizen comments that did not receive officer/admin response.

    Args:
        now: Optional datetime override for deterministic tests.

    Returns:
        Number of comments escalated in this run.
    """
    now = now or datetime.utcnow()

    overdue_comments = GrievanceComment.query.filter(
        GrievanceComment.user_role == 'CITIZEN',
        GrievanceComment.response_deadline.isnot(None),
        GrievanceComment.response_deadline < now,
        GrievanceComment.escalated.is_(False),
    ).all()

    escalated_count = 0
    updated_any_comment = False
    pending_email_jobs = []

    for comment in overdue_comments:
        grievance = Grievance.query.get(comment.grievance_id)
        if not grievance:
            continue

        officer_response = GrievanceComment.query.filter(
            GrievanceComment.grievance_id == comment.grievance_id,
            GrievanceComment.created_at > comment.created_at,
            GrievanceComment.user_role.in_(['OFFICER', 'ADMIN']),
        ).first()

        if officer_response:
            comment.escalated = True
            updated_any_comment = True
            continue

        current_officer = None
        if comment.notified_officer_id:
            current_officer = User.query.get(comment.notified_officer_id)
        if not current_officer and grievance.assigned_officer_id:
            current_officer = User.query.get(grievance.assigned_officer_id)
        if not current_officer:
            current_officer = User.query.filter(
                User.role.in_(OFFICER_ROLE_VALUES),
                User.department == grievance.assigned_department,
            ).order_by(User.created_at.asc(), User.id.asc()).first()

        if not current_officer:
            continue

        superior = get_escalation_recipient(current_officer, grievance)
        if not superior:
            continue

        comment.escalated = True
        comment.escalated_at = now
        comment.escalated_to_officer_id = superior.id
        _create_escalation_log(
            grievance_id=grievance.id,
            from_officer=current_officer,
            to_officer=superior,
            reason='No response within 24 hours',
            escalation_type='auto',
        )

        NotificationService.queue_notification(
            user_id=superior.id,
            title=f'⚠️ Escalated: Grievance #{grievance.id}',
            message=f'Citizen comment has not been responded by {current_officer.name}. Immediate action required.',
            notification_type='escalation',
            related_grievance_id=grievance.id,
        )

        pending_email_jobs.append((
            EmailService.send_escalation_alert,
            {
                'superior_email': superior.email,
                'superior_name': superior.name,
                'grievance_id': grievance.id,
                'current_officer_name': current_officer.name,
                'comment_text': comment.comment_text,
                'comment_sent_at': _format_timestamp(comment.notification_sent_at),
                'response_deadline': _format_timestamp(comment.response_deadline),
                'escalation_type': 'auto',
            }
        ))
        pending_email_jobs.append((
            EmailService.send_escalation_notice_to_officer,
            {
                'officer_email': current_officer.email,
                'officer_name': current_officer.name,
                'grievance_id': grievance.id,
                'escalated_to_name': superior.name,
            }
        ))

        escalated_count += 1
        updated_any_comment = True

    if updated_any_comment:
        try:
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            print(f"Failed to persist escalations: {db_error}")
            return 0

    _send_pending_emails(pending_email_jobs)

    if escalated_count > 0:
        print(f"✓ Escalated {escalated_count} overdue comments")

    return escalated_count


def escalate_comment_manually(comment_id):
    """Manually escalate a specific citizen comment."""
    comment = GrievanceComment.query.get(comment_id)
    if not comment:
        return {'success': False, 'message': 'Comment not found'}

    if comment.user_role != 'CITIZEN':
        return {'success': False, 'message': 'Only citizen comments can be escalated'}

    if comment.escalated:
        return {'success': False, 'message': 'Comment already escalated'}

    grievance = Grievance.query.get(comment.grievance_id)
    if not grievance:
        return {'success': False, 'message': 'Grievance not found'}

    current_officer = None
    if comment.notified_officer_id:
        current_officer = User.query.get(comment.notified_officer_id)
    if not current_officer and grievance.assigned_officer_id:
        current_officer = User.query.get(grievance.assigned_officer_id)
    if not current_officer:
        return {'success': False, 'message': 'No officer assigned'}

    superior = get_escalation_recipient(current_officer, grievance)
    if not superior:
        return {'success': False, 'message': 'No superior officer found for escalation'}

    comment.escalated = True
    comment.escalated_at = datetime.utcnow()
    comment.escalated_to_officer_id = superior.id
    _create_escalation_log(
        grievance_id=grievance.id,
        from_officer=current_officer,
        to_officer=superior,
        reason='Manual escalation by admin',
        escalation_type='manual',
    )

    NotificationService.queue_notification(
        user_id=superior.id,
        title=f'⚠️ Escalated: Grievance #{grievance.id}',
        message=f'Citizen comment has been manually escalated from {current_officer.name}.',
        notification_type='escalation',
        related_grievance_id=grievance.id,
    )

    try:
        db.session.commit()
    except Exception as db_error:
        db.session.rollback()
        return {'success': False, 'message': f'Failed to persist escalation: {db_error}'}

    _send_pending_emails([
        (
            EmailService.send_escalation_alert,
            {
                'superior_email': superior.email,
                'superior_name': superior.name,
                'grievance_id': grievance.id,
                'current_officer_name': current_officer.name,
                'comment_text': comment.comment_text,
                'comment_sent_at': _format_timestamp(comment.notification_sent_at),
                'response_deadline': _format_timestamp(comment.response_deadline),
                'escalation_type': 'manual',
            },
        ),
        (
            EmailService.send_escalation_notice_to_officer,
            {
                'officer_email': current_officer.email,
                'officer_name': current_officer.name,
                'grievance_id': grievance.id,
                'escalated_to_name': superior.name,
            },
        ),
    ])

    return {
        'success': True,
        'message': f'Comment escalated to {superior.name}',
        'escalated_to': superior.name,
    }
