from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from backend.models import Grievance, GrievanceUpdate, GrievanceComment, FraudReport, User, RoleHierarchy
from backend.models_addons import AuditLog, GrievanceRating, DepartmentCorrectionLog
from backend.extensions import db
from backend.config import Config
from backend.routes.auth import get_current_user_from_token
from backend.services.classifier import classifier
from backend.services.content_moderator import ContentModerator
from backend.services.email_service import EmailService
from backend.services.notification_service import NotificationService
from backend.services.comment_escalation import check_and_escalate_comments, escalate_comment_manually
from backend.services.fraud_service import notify_fraud_report, review_fraud_report
from backend.services.audit_service import log_audit
from backend.security import require_firewall, SecurityFirewall, SecurityLogger
from backend.utils.roles import ADMIN_ROLE_VALUES, OFFICER_ROLE_VALUES, canonical_role, is_role
from backend.utils.workflow import can_view_grievance, can_officer_act_on_grievance
from backend.utils.validation import (
    ValidationError,
    validate_comment_text,
    validate_complaint_text,
    validate_location,
    validate_update_message,
)

grievances_bp = Blueprint('grievances', __name__)

@grievances_bp.route('/predict-department', methods=['POST'])
def predict_department():
    """
    Predict department for a complaint text (for dynamic UI updates)
    Required: complaint_text
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response

        data = request.get_json() or {}
        complaint_text = data.get('complaint_text')
        
        if not complaint_text:
            return jsonify({'error': 'Complaint text is required'}), 400

        is_valid, sanitized_text, error = SecurityFirewall.validate_input(complaint_text, 'complaint_text')
        if not is_valid:
            return jsonify({'error': error or 'Invalid complaint text'}), 400
        
        # Predict department with confidence metadata
        prediction = classifier.predict_with_confidence(sanitized_text)
        predicted_department = prediction['department']
        prediction_confidence = float(prediction.get('confidence') or 0.0)
        
        # Enforce allowed departments
        if predicted_department not in Config.ALLOWED_DEPARTMENTS:
            predicted_department = Config.DEFAULT_DEPARTMENT
            prediction_confidence = 0.0
        
        # Images are always optional — no mandatory requirement
        images_required = False
        requires_manual_review = (
            (not prediction.get('model_loaded'))
            or (prediction_confidence < Config.ML_AUTO_ASSIGN_CONFIDENCE_THRESHOLD)
        )
        
        return jsonify({
            'department': predicted_department,
            'images_required': images_required,
            'prediction_confidence': prediction_confidence,
            'prediction_confidence_pct': round(prediction_confidence * 100, 2),
            'top_candidates': prediction.get('top_candidates', []),
            'requires_manual_review': requires_manual_review,
            'routing_decision': 'manual_review' if requires_manual_review else 'auto_assign',
            'auto_assign_threshold': Config.ML_AUTO_ASSIGN_CONFIDENCE_THRESHOLD,
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/submit', methods=['POST'])
@require_firewall(max_requests=20, window_minutes=60)  # Max 20 grievances per hour
def submit_grievance():
    """
    Submit a new grievance
    Required: complaint_text
    Optional: location
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['CITIZEN'])
        if auth_response:
            return auth_response

        data = request.get_json() or {}
        complaint_text = data.get('complaint_text')
        location = data.get('location', '')
        images = data.get('images', [])

        try:
            complaint_text = validate_complaint_text(complaint_text)
            location = validate_location(location)
        except ValidationError as validation_error:
            return jsonify({'error': str(validation_error)}), 400

        moderation = ContentModerator.moderate_content(complaint_text)
        if ContentModerator.should_block_submission(moderation):
            return jsonify({
                'error': ContentModerator.get_user_warning_message(moderation),
                'moderation': moderation,
            }), 400

        # Predict department using ML with confidence.
        prediction = classifier.predict_with_confidence(complaint_text)
        predicted_department = prediction['department']
        prediction_confidence = float(prediction.get('confidence') or 0.0)
        prediction_source = prediction.get('source', 'fallback')
        
        # Enforce allowed departments
        if predicted_department not in Config.ALLOWED_DEPARTMENTS:
            predicted_department = Config.DEFAULT_DEPARTMENT
            prediction_confidence = 0.0
            requires_manual_triage = True
        else:
            requires_manual_triage = (
                (not prediction.get('model_loaded'))
                or (prediction_confidence < Config.ML_AUTO_ASSIGN_CONFIDENCE_THRESHOLD)
            )
        
        if images and len(images) > 5:
            return jsonify({'error': 'Maximum 5 images allowed'}), 400

        # Get complainant info from user profile
        complainant_dob = user.date_of_birth
        complainant_gender = user.gender
        
        # Store images as JSON
        images_json = json.dumps(images) if images else None

        routing_status = 'Assigned to Department'
        assigned_department = predicted_department
        routing_message = f'Your complaint has been assigned to {predicted_department} department for review.'
        triage_reason = None

        if requires_manual_triage:
            routing_status = 'Manual Review Required'
            assigned_department = Config.ML_MANUAL_REVIEW_DEPARTMENT
            routing_message = (
                f'Your complaint has been routed to manual triage because model confidence '
                f'({prediction_confidence * 100:.1f}%) is below the auto-assign threshold '
                f'({Config.ML_AUTO_ASSIGN_CONFIDENCE_THRESHOLD * 100:.1f}%). '
                f'Admin review is pending.'
            )
            triage_reason = (
                f'Low model confidence ({prediction_confidence * 100:.1f}%) for '
                f'predicted department "{predicted_department}"'
            )
        
        # Compute SLA deadline
        now = datetime.utcnow()
        from sqlalchemy import func
        # Case-insensitive lookup for department config
        dept_config = RoleHierarchy.query.filter(func.lower(RoleHierarchy.department) == func.lower(assigned_department)).first()
        sla_hours = dept_config.sla_hours if dept_config and dept_config.sla_hours else 48
        sla_deadline = now + timedelta(hours=sla_hours)

        # Create grievance
        grievance = Grievance(
            user_id=user.id,
            complaint_text=complaint_text,
            predicted_department=predicted_department,
            assigned_department=assigned_department,
            prediction_confidence=prediction_confidence,
            prediction_source=prediction_source,
            requires_manual_triage=requires_manual_triage,
            triage_reason=triage_reason,
            status='Received',
            location=location,
            images=images_json,
            complainant_dob=complainant_dob,
            complainant_gender=complainant_gender,
            moderation_score=moderation.get('score', 0),
            moderation_severity=moderation.get('severity'),
            moderation_flags=json.dumps(moderation.get('flags', [])),
            # SLA tracking
            sla_hours=sla_hours,
            sla_deadline=sla_deadline,
        )
        
        db.session.add(grievance)
        db.session.flush()  # Get the grievance ID
        
        # Create first update - Received
        update1 = GrievanceUpdate(
            grievance_id=grievance.id,
            status='Received',
            message='Your complaint has been received and is being processed.',
            updated_by_role='SYSTEM',
            updated_by_name='Smart Grievance System'
        )
        db.session.add(update1)
        
        # Create second update - Assigned to Department
        update2 = GrievanceUpdate(
            grievance_id=grievance.id,
            status=routing_status,
            message=routing_message,
            updated_by_role='SYSTEM',
            updated_by_name='Smart Grievance System'
        )
        db.session.add(update2)
        
        # Update grievance status
        grievance.status = routing_status

        if requires_manual_triage:
            admins = User.query.filter(User.role.in_(ADMIN_ROLE_VALUES)).all()
            for admin in admins:
                NotificationService.queue_notification(
                    user_id=admin.id,
                    title=f'Manual ML Triage Needed - Grievance #{grievance.id}',
                    message=(
                        f'Predicted: {predicted_department} | '
                        f'Confidence: {prediction_confidence * 100:.1f}% | '
                        f'Citizen: {user.name}'
                    ),
                    notification_type='triage_review',
                    related_grievance_id=grievance.id,
                    is_read=False,
                )
        elif ContentModerator.should_notify_admin(moderation):
            admins = User.query.filter(User.role.in_(ADMIN_ROLE_VALUES)).all()
            for admin in admins:
                NotificationService.queue_notification(
                    user_id=admin.id,
                    title=f'Content Review Needed - Grievance #{grievance.id}',
                    message=ContentModerator.get_user_warning_message(moderation),
                    notification_type='content_moderation',
                    related_grievance_id=grievance.id,
                    is_read=False,
                )


        
        db.session.commit()
        
        # Send email notification
        EmailService.send_grievance_notification(
            user.email,
            grievance.id,
            predicted_department,
            routing_status,
            routing_message
        )
        
        log_audit(
            user.id,
            'create_grievance',
            'grievance',
            grievance.id,
            json.dumps({
                'department': predicted_department,
                'prediction_confidence': prediction_confidence,
                'routing_status': routing_status,
                'requires_manual_triage': requires_manual_triage,
            })
        )
        
        response_data = {
            'message': 'Grievance submitted successfully',
            'grievance_id': grievance.id,
            'department': predicted_department,
            'status': grievance.status,
            'routing_decision': 'manual_review' if requires_manual_triage else 'auto_assign',
            'prediction_confidence': prediction_confidence,
            'auto_assign_threshold': Config.ML_AUTO_ASSIGN_CONFIDENCE_THRESHOLD,
            'sla_deadline': sla_deadline.isoformat(),
        }
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/my-grievances', methods=['GET'])
def get_my_grievances():
    """
    Get all grievances for current user
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        grievances = Grievance.query.filter_by(user_id=user.id).order_by(Grievance.created_at.desc()).all()
        
        return jsonify({
            'grievances': [g.to_dict() for g in grievances]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/<int:grievance_id>', methods=['GET'])
def get_grievance(grievance_id):
    """
    Get grievance details with timeline
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        grievance = Grievance.query.get(grievance_id)
        
        if not grievance:
            return jsonify({'error': 'Grievance not found'}), 404
        
        allowed, error = can_view_grievance(user, grievance)
        if not allowed:
            return jsonify({'error': error}), 403

        include_officer = canonical_role(user.role) in ['OFFICER', 'ADMIN']
        return jsonify({
            'grievance': grievance.to_dict(include_updates=True, include_comments=True, include_officer=include_officer)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/department/<department>', methods=['GET'])
def get_department_grievances(department):
    """
    Get all grievances for a department (Officer only)
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['OFFICER', 'ADMIN'])
        if auth_response:
            return auth_response
        
        # Officers can only see their department
        if is_role(user, 'OFFICER') and user.department != department:
            return jsonify({'error': 'Unauthorized to view this department'}), 403
        
        grievances = Grievance.query.filter_by(
            assigned_department=department
        ).order_by(Grievance.created_at.desc()).all()
        
        return jsonify({
            'grievances': [g.to_dict() for g in grievances]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/<int:grievance_id>/update', methods=['POST'])
def update_grievance(grievance_id):
    """
    Update grievance status (Officer/Admin only)
    Required: status, message
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['OFFICER', 'ADMIN'])
        if auth_response:
            return auth_response

        data = request.get_json() or {}
        new_status = data.get('status')
        message = data.get('message')
        
        if not new_status or not message:
            return jsonify({'error': 'status and message are required'}), 400

        try:
            message = validate_update_message(message)
        except ValidationError as validation_error:
            return jsonify({'error': str(validation_error)}), 400
        
        # Valid statuses
        valid_statuses = [
            'Received',
            'Assigned to Department',
            'Under Progress',
            'Investigation',
            'Reviewed',
            'Resolved',
            'Closed'
        ]
        
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        grievance = Grievance.query.get(grievance_id)
        
        if not grievance:
            return jsonify({'error': 'Grievance not found'}), 404
        
        if is_role(user, 'OFFICER'):
            allowed, error = can_officer_act_on_grievance(user, grievance)
            if not allowed:
                return jsonify({'error': error}), 403
        
        # Store old status for notification
        old_status = grievance.status
        
        # Create update entry
        update = GrievanceUpdate(
            grievance_id=grievance.id,
            status=new_status,
            message=message,
            updated_by_role=user.role,
            updated_by_name=user.name
        )
        db.session.add(update)
        
        # Update grievance status
        grievance.status = new_status
        grievance.updated_at = datetime.utcnow()
        grievance.last_action_at = datetime.utcnow()

        # Clear SLA breach on terminal statuses (resolved/closed)
        if new_status in ('Resolved', 'Closed'):
            grievance.sla_breached = False

        # First officer action on an unassigned grievance claims ownership.
        if is_role(user, 'OFFICER') and not grievance.assigned_officer_id:
            grievance.assigned_officer_id = user.id
        
        # Assign officer if status is "Assigned to Department" and not already assigned
        if new_status == 'Assigned to Department' and not grievance.assigned_officer_id:
            grievance.assigned_officer_id = user.id
            
        # ── ML Correction Logging ──
        if 'assigned_department' in data and data['assigned_department'] != grievance.predicted_department:
            # Check if this correction was already logged to avoid duplicates
            existing_correction = DepartmentCorrectionLog.query.filter_by(
                grievance_id=grievance.id,
                corrected_department=data['assigned_department']
            ).first()
            
            if not existing_correction:
                correction = DepartmentCorrectionLog(
                    grievance_id=grievance.id,
                    predicted_department=grievance.predicted_department or "Unknown",
                    corrected_department=data['assigned_department'],
                    prediction_confidence=0.0, # Placeholder or fetch if stored
                    corrected_by_user_id=user.id,
                    reason=message or "Manual department correction"
                )
                db.session.add(correction)

        if 'assigned_department' in data:
            new_dept = data['assigned_department']
            if new_dept not in Config.ALLOWED_DEPARTMENTS and new_dept != Config.ML_MANUAL_REVIEW_DEPARTMENT:
                return jsonify({
                    'error': f'Invalid department: {new_dept}. Allowed departments: {", ".join(Config.ALLOWED_DEPARTMENTS)}'
                }), 400
            grievance.assigned_department = new_dept
        
        db.session.commit()
        
        # Send email notification to citizen with detailed update
        citizen = User.query.get(grievance.user_id)
        if citizen:
            EmailService.send_status_update_notification(
                user_email=citizen.email,
                user_name=citizen.name,
                grievance_id=grievance.id,
                old_status=old_status,
                new_status=new_status,
                update_message=message,
                department=grievance.assigned_department,
                officer_name=user.name
            )
        
        log_audit(user.id, 'update_grievance', 'grievance', grievance_id, json.dumps({'old_status': old_status, 'new_status': new_status}))
        
        return jsonify({
            'message': 'Grievance updated successfully',
            'grievance': grievance.to_dict(include_updates=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/<int:grievance_id>/comments', methods=['GET'])
def get_comments(grievance_id):
    """
    Get all comments for a grievance
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        grievance = Grievance.query.get(grievance_id)
        
        if not grievance:
            return jsonify({'error': 'Grievance not found'}), 404
        
        allowed, error = can_view_grievance(user, grievance)
        if not allowed:
            return jsonify({'error': error}), 403
        
        comments = GrievanceComment.query.filter_by(
            grievance_id=grievance_id
        ).order_by(GrievanceComment.created_at.asc()).all()
        
        return jsonify({
            'comments': [comment.to_dict() for comment in comments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/<int:grievance_id>/comments', methods=['POST'])
def add_comment(grievance_id):
    """
    Add a comment to a grievance (Citizen or Officer)
    Required: comment_text
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        data = request.get_json() or {}
        comment_text = data.get('comment_text')
        try:
            comment_text = validate_comment_text(comment_text)
        except ValidationError as validation_error:
            return jsonify({'error': str(validation_error)}), 400
        
        grievance = Grievance.query.get(grievance_id)
        
        if not grievance:
            return jsonify({'error': 'Grievance not found'}), 404
        
        if is_role(user, 'CITIZEN'):
            if grievance.user_id != user.id:
                return jsonify({'error': 'Unauthorized to comment on this grievance'}), 403
        elif is_role(user, 'OFFICER'):
            allowed, error = can_officer_act_on_grievance(user, grievance)
            if not allowed:
                return jsonify({'error': error}), 403
            if not grievance.assigned_officer_id:
                grievance.assigned_officer_id = user.id
                grievance.updated_at = datetime.utcnow()
        
        # Create comment
        comment = GrievanceComment(
            grievance_id=grievance_id,
            user_id=user.id,
            comment_text=comment_text,
            user_role=user.role,
            user_name=user.name
        )
        
        db.session.add(comment)
        pending_email_jobs = []
        
        # Prepare notification recipients and escalation metadata before commit.
        if is_role(user, 'CITIZEN'):
            # Notify ONLY the currently assigned officer (not all officers)
            if grievance.assigned_officer_id:
                assigned_officer = User.query.get(grievance.assigned_officer_id)
                
                if assigned_officer:
                    # Track notification for escalation
                    comment.notified_officer_id = assigned_officer.id
                    comment.notification_sent_at = datetime.utcnow()
                    comment.response_deadline = datetime.utcnow() + timedelta(hours=24)  # 24 hours to respond

                    pending_email_jobs.append((
                        EmailService.send_citizen_comment_alert,
                        {
                            'officer_email': assigned_officer.email,
                            'officer_name': assigned_officer.name,
                            'grievance_id': grievance_id,
                            'comment_text': comment_text,
                            'response_hours': 24,
                        }
                    ))
                    
                    # Create in-app notification
                    NotificationService.queue_notification(
                        user_id=assigned_officer.id,
                        title=f'New Comment on Grievance #{grievance_id}',
                        message=f'Citizen has commented: "{comment_text[:100]}..." - Response required within 24 hours.',
                        notification_type='comment',
                        related_grievance_id=grievance_id,
                    )
            else:
                # If no specific officer assigned, notify department head
                dept_head = User.query.filter(
                    User.department == grievance.assigned_department,
                    User.role.in_(OFFICER_ROLE_VALUES)
                ).order_by(User.id.asc()).first()  # Get first officer as fallback
                
                if dept_head:
                    comment.notified_officer_id = dept_head.id
                    comment.notification_sent_at = datetime.utcnow()
                    comment.response_deadline = datetime.utcnow() + timedelta(hours=24)

                    pending_email_jobs.append((
                        EmailService.send_citizen_comment_alert,
                        {
                            'officer_email': dept_head.email,
                            'officer_name': dept_head.name,
                            'grievance_id': grievance_id,
                            'comment_text': comment_text,
                            'response_hours': 24,
                        }
                    ))
                    NotificationService.queue_notification(
                        user_id=dept_head.id,
                        title=f'New Comment on Grievance #{grievance_id}',
                        message=f'Citizen has commented: "{comment_text[:100]}..." - Response required within 24 hours.',
                        notification_type='comment',
                        related_grievance_id=grievance_id,
                    )
        else:
            # Notify citizen
            citizen = User.query.get(grievance.user_id)
            if citizen:
                pending_email_jobs.append((
                    EmailService.send_officer_reply_alert,
                    {
                        'citizen_email': citizen.email,
                        'citizen_name': citizen.name,
                        'grievance_id': grievance_id,
                        'officer_name': user.name,
                        'department': grievance.assigned_department,
                        'comment_text': comment_text,
                    }
                ))

        db.session.commit()

        for email_fn, kwargs in pending_email_jobs:
            try:
                email_fn(**kwargs)
            except Exception as email_error:
                print(f"Failed to send comment notification email: {email_error}")
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/check-comment-escalations', methods=['POST'])
def check_comment_escalations():
    """
    Check for overdue comments and escalate them (Admin/System only)
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        escalated_count = check_and_escalate_comments()
        
        return jsonify({
            'message': 'Escalation check completed',
            'escalated_count': escalated_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grievances_bp.route('/comments/<int:comment_id>/escalate', methods=['POST'])
def manually_escalate_comment(comment_id):
    """
    Manually escalate a specific comment (Admin only)
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        result = escalate_comment_manually(comment_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@grievances_bp.route('/<int:grievance_id>/report-fraud', methods=['POST'])
def report_fraud(grievance_id):
    """Submit an officer fraud report for admin review."""
    try:
        officer, auth_response = get_current_user_from_token(
            return_error=True,
            required_roles=['OFFICER'],
        )
        if auth_response:
            return auth_response

        grievance = Grievance.query.get(grievance_id)
        if not grievance:
            return jsonify({'error': 'Grievance not found'}), 404

        allowed, error = can_officer_act_on_grievance(officer, grievance)
        if not allowed:
            return jsonify({'error': error}), 403

        data = request.get_json() or {}
        fraud_type = data.get('fraud_type')
        description = data.get('description')
        if not isinstance(fraud_type, str) or not fraud_type.strip():
            return jsonify({'error': 'fraud_type is required'}), 400
        if not isinstance(description, str) or not description.strip():
            return jsonify({'error': 'description is required'}), 400

        report = FraudReport(
            grievance=grievance,
            grievance_id=grievance.id,
            reported_by_officer_id=officer.id,
            complainant_user_id=grievance.user_id,
            fraud_type=fraud_type.strip()[:50],
            description=description.strip(),
            evidence=(
                json.dumps(data['evidence'])
                if isinstance(data.get('evidence'), (dict, list))
                else data.get('evidence')
            ),
            site_visit_notes=(
                data.get('site_visit_notes').strip()
                if isinstance(data.get('site_visit_notes'), str)
                else None
            ),
        )
        grievance.status = 'Suspended - Fraud Investigation'
        db.session.add(report)
        db.session.add(GrievanceUpdate(
            grievance_id=grievance.id,
            status=grievance.status,
            message=f"Fraud report submitted by Officer {officer.name}.",
            updated_by_role='OFFICER',
            updated_by_name=officer.name,
        ))
        notify_fraud_report(report, officer)

        return jsonify({
            'message': 'Fraud report submitted for admin review',
            'fraud_report_id': report.id,
            'fraud_report': report.to_dict(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@grievances_bp.route('/fraud-reports', methods=['GET'])
def get_fraud_reports():
    """List fraud reports for admin review."""
    try:
        user, auth_response = get_current_user_from_token(
            return_error=True,
            required_roles=['ADMIN'],
        )
        if auth_response:
            return auth_response

        reports = FraudReport.query.order_by(FraudReport.created_at.desc()).all()
        return jsonify({'fraud_reports': [report.to_dict() for report in reports]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@grievances_bp.route('/fraud-reports/<int:report_id>/action', methods=['POST'])
def action_fraud_report(report_id):
    """Apply an admin decision to a fraud report."""
    try:
        admin_user, auth_response = get_current_user_from_token(
            return_error=True,
            required_roles=['ADMIN'],
        )
        if auth_response:
            return auth_response

        data = request.get_json() or {}
        action = data.get('action')
        if action not in ('verify', 'dismiss', 'suspend'):
            return jsonify({'error': 'Invalid action. Must be verify, dismiss, or suspend'}), 400

        report = FraudReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Fraud report not found'}), 404

        grievance = review_fraud_report(
            report,
            admin_user,
            action,
            admin_notes=data.get('admin_notes', ''),
            suspend_user=bool(data.get('suspend_user')),
        )
        return jsonify({
            'message': f'Fraud report {action}ed successfully',
            'report_status': report.status,
            'grievance_status': grievance.status,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
