from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from backend.models import User, Grievance, GrievanceUpdate, Notification
from backend.models_addons import DepartmentCorrectionLog
from backend.extensions import db
from backend.config import Config
from backend.routes.auth import get_current_user_from_token
from backend.services.email_service import EmailService
from backend.services.notification_service import NotificationService
from backend.services.model_retrain import retrain_model, get_retrain_status
from backend.security import SecurityFirewall
from backend.utils.validation import ValidationError, normalize_phone, validate_name
from backend.utils.roles import OFFICER_ROLE_VALUES, is_role

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/create-officer', methods=['POST'])
def create_officer():
    """
    Create a new officer account (Admin only)
    Required: name, email, phone, password, department
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'password', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        is_valid_email, normalized_email, email_error = SecurityFirewall.validate_email_address(data['email'])
        if not is_valid_email:
            return jsonify({'error': f'Invalid email: {email_error}'}), 400

        is_valid_department, sanitized_department, department_error = SecurityFirewall.validate_input(
            data['department'],
            'department'
        )
        if not is_valid_department:
            return jsonify({'error': department_error or 'Invalid department'}), 400

        is_strong, password_error = SecurityFirewall.check_password_strength(data['password'])
        if not is_strong:
            return jsonify({'error': password_error}), 400

        try:
            validated_name = validate_name(data['name'])
            validated_phone = normalize_phone(data['phone'])
        except ValidationError as validation_error:
            return jsonify({'error': str(validation_error)}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=normalized_email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400

        existing_phone = User.query.filter_by(phone=validated_phone).first()
        if existing_phone:
            return jsonify({'error': 'Phone number already registered'}), 400
        
        # Create officer
        officer = User(
            name=validated_name,
            email=normalized_email,
            phone=validated_phone,
            role='OFFICER',
            department=sanitized_department,
            email_verified=True,  # Auto-verify officers
            phone_verified=True
        )
        officer.set_password(data['password'])
        
        db.session.add(officer)
        db.session.commit()
        
        return jsonify({
            'message': 'Officer created successfully',
            'officer': officer.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/officers', methods=['GET'])
def get_officers():
    """
    Get all officers (Admin only)
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        officers = User.query.filter(User.role.in_(OFFICER_ROLE_VALUES)).all()
        
        return jsonify({
            'officers': [officer.to_dict() for officer in officers]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
def get_users():
    """
    Get all users/citizens (Admin only)
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        # Get all citizens
        citizens = User.query.filter_by(role='CITIZEN').all()
        
        # Get grievance count for each citizen
        users_data = []
        for citizen in citizens:
            user_dict = citizen.to_dict()
            grievance_count = Grievance.query.filter_by(user_id=citizen.id).count()
            user_dict['grievance_count'] = grievance_count
            users_data.append(user_dict)
        
        return jsonify({
            'users': users_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """
    Get system analytics (Admin only)
    Returns:
    - counts_by_status
    - counts_by_department
    - avg_resolution_time_days
    - total_grievances
    - total_users
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        # Count by status
        status_counts = db.session.query(
            Grievance.status,
            func.count(Grievance.id)
        ).group_by(Grievance.status).all()
        
        counts_by_status = {status: count for status, count in status_counts}
        
        # Count by department (authoritative 5 allowed departments)
        dept_counts = db.session.query(
            Grievance.assigned_department,
            func.count(Grievance.id)
        ).group_by(Grievance.assigned_department).all()
        
        counts_by_department = {dept: 0 for dept in Config.ALLOWED_DEPARTMENTS}
        for dept, count in dept_counts:
            if dept in counts_by_department:
                counts_by_department[dept] = count
            elif dept == Config.ML_MANUAL_REVIEW_DEPARTMENT and count > 0:
                counts_by_department[dept] = count
        
        # Calculate average resolution time for closed/resolved grievances
        resolved_grievances = Grievance.query.filter(
            Grievance.status.in_(['Resolved', 'Closed'])
        ).all()
        
        total_resolution_time = 0
        resolved_count = 0
        
        for grievance in resolved_grievances:
            if grievance.created_at and grievance.updated_at:
                resolution_time = (grievance.updated_at - grievance.created_at).total_seconds()
                total_resolution_time += resolution_time
                resolved_count += 1
        
        avg_resolution_time_days = 0
        if resolved_count > 0:
            avg_resolution_time_seconds = total_resolution_time / resolved_count
            avg_resolution_time_days = round(avg_resolution_time_seconds / (24 * 3600), 2)
        
        # Total counts
        total_grievances = Grievance.query.count()
        total_users = User.query.filter_by(role='CITIZEN').count()
        total_officers = User.query.filter(User.role.in_(OFFICER_ROLE_VALUES)).count()
        
        # Fraud analytics
        pending_fraud_reports = FraudReport.query.filter_by(status='Pending').count()
        total_fraud_reports = FraudReport.query.count()
        verified_fraud_reports = FraudReport.query.filter_by(status='Verified').count()
        total_suspended_users = User.query.filter_by(account_suspended=True).count()

        # SLA analytics
        sla_breached_count = Grievance.query.filter_by(sla_breached=True).count()
        sla_breached_active = Grievance.query.filter(
            Grievance.sla_breached.is_(True),
            ~Grievance.status.in_(['Resolved', 'Closed'])
        ).count()

        # Moderation analytics
        flagged_grievances = Grievance.query.filter_by(is_flagged=True).count()

        return jsonify({
            'counts_by_status': counts_by_status,
            'counts_by_department': counts_by_department,
            'avg_resolution_time_days': avg_resolution_time_days,
            'total_grievances': total_grievances,
            'total_users': total_users,
            'total_officers': total_officers,
            'fraud': {
                'pending_reports': pending_fraud_reports,
                'total_reports': total_fraud_reports,
                'verified_reports': verified_fraud_reports,
                'suspended_users': total_suspended_users,
            },
            'sla': {
                'total_breached': sla_breached_count,
                'active_breached': sla_breached_active,
            },
            'moderation': {
                'flagged_grievances': flagged_grievances,
            },
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/all-grievances', methods=['GET'])
def get_all_grievances():
    """
    Get all grievances with complete user and officer information (Admin only)
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        # Get query parameters for filtering
        status = request.args.get('status')
        department = request.args.get('department')
        
        query = Grievance.query
        
        if status:
            query = query.filter_by(status=status)
        
        if department:
            query = query.filter_by(assigned_department=department)
        
        grievances = query.order_by(Grievance.created_at.desc()).all()
        
        # Build detailed grievance data with complete user and officer information
        grievances_data = []
        for g in grievances:
            grievance_dict = g.to_dict(include_officer=True)
            
            # Add complete complainant (user) information
            complainant = User.query.get(g.user_id)
            if complainant:
                grievance_dict['complainant'] = {
                    'id': complainant.id,
                    'name': complainant.name,
                    'email': complainant.email,
                    'phone': complainant.phone,
                    'residential_address': complainant.residential_address,
                    'residential_city': complainant.residential_city,
                    'residential_state': complainant.residential_state,
                    'residential_pincode': complainant.residential_pincode,
                    'date_of_birth': complainant.date_of_birth,
                    'gender': complainant.gender,
                    'email_verified': complainant.email_verified,
                    'phone_verified': complainant.phone_verified,
                    'created_at': complainant.created_at.isoformat() if complainant.created_at else None
                }
            
            grievances_data.append(grievance_dict)
        
        return jsonify({
            'grievances': grievances_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments', methods=['GET'])
def get_departments():
    """
    Get list of all active allowed departments
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        return jsonify({
            'departments': Config.ALLOWED_DEPARTMENTS
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/assign-officer', methods=['POST'])
def assign_officer():
    """
    Assign an officer to a grievance (Admin only)
    Required: grievance_id, officer_id
    Sends email notification to officer and user
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        data = request.get_json() or {}
        grievance_id = data.get('grievance_id')
        officer_id = data.get('officer_id')
        
        if not grievance_id or not officer_id:
            return jsonify({'error': 'grievance_id and officer_id are required'}), 400
        
        # Get grievance
        grievance = Grievance.query.get(grievance_id)
        if not grievance:
            return jsonify({'error': 'Grievance not found'}), 404
        
        # Get officer
        officer = User.query.get(officer_id)
        if not officer or not is_role(officer, 'OFFICER'):
            return jsonify({'error': 'Officer not found'}), 404

        if not officer.department:
            return jsonify({'error': 'Officer department is required for assignment'}), 400

        manual_triage_case = (
            grievance.requires_manual_triage
            or grievance.status == 'Manual Review Required'
            or grievance.assigned_department == Config.ML_MANUAL_REVIEW_DEPARTMENT
        )
        if not manual_triage_case and officer.department != grievance.assigned_department:
            return jsonify({
                'error': (
                    'Officer department mismatch. '
                    f'Grievance is assigned to {grievance.assigned_department}.'
                )
            }), 400
        
        # Get citizen
        citizen = User.query.get(grievance.user_id)
        if not citizen:
            return jsonify({'error': 'Citizen not found'}), 404
        
        # Store old assignment context for notifications
        old_status = grievance.status
        
        previous_assigned_department = grievance.assigned_department
        # Special logic for manual triage: correction is defined as difference between ML PREDICTION and FINAL ASSIGNMENT
        if previous_assigned_department == Config.ML_MANUAL_REVIEW_DEPARTMENT:
            department_corrected = (officer.department != grievance.predicted_department)
        else:
            department_corrected = (officer.department != previous_assigned_department)

        # Assign officer
        grievance.assigned_officer_id = officer_id
        grievance.assigned_department = officer.department
        grievance.status = 'Assigned to Department'
        grievance.requires_manual_triage = False
        grievance.triage_reason = None
        grievance.updated_at = datetime.utcnow()
        
        # Create update entry
        assignment_message = (
            f'Case assigned to Officer {officer.name} ({officer.designation or "Officer"}) by Admin.'
        )
        if department_corrected:
            assignment_message = (
                f'Case assigned to Officer {officer.name} ({officer.designation or "Officer"}) by Admin. '
                f'Department corrected from {previous_assigned_department} to {officer.department}.'
            )

        update = GrievanceUpdate(
            grievance_id=grievance.id,
            status='Assigned to Department',
            message=assignment_message,
            updated_by_role='ADMIN',
            updated_by_name=user.name
        )
        db.session.add(update)

        if department_corrected:
            correction_log = DepartmentCorrectionLog(
                grievance_id=grievance.id,
                predicted_department=grievance.predicted_department,
                corrected_department=officer.department,
                prediction_confidence=grievance.prediction_confidence,
                corrected_by_user_id=user.id,
                assigned_officer_id=officer.id,
                reason='Admin selected officer department during triage review',
            )
            db.session.add(correction_log)
        
        # Create in-app notification for officer
        NotificationService.queue_notification(
            user_id=officer_id,
            title=f'🚨 New Case Assigned - Grievance #{grievance.id}',
            message=f'You have been assigned a new case in {grievance.assigned_department} department. Complainant: {citizen.name}. Please review and take action.',
            notification_type='assignment',
            related_grievance_id=grievance.id,
            is_read=False,
        )
        
        # Create in-app notification for citizen
        NotificationService.queue_notification(
            user_id=citizen.id,
            title=f'Officer Assigned - Grievance #{grievance.id}',
            message=f'Your complaint has been assigned to {officer.name} ({officer.designation or "Officer"}) for resolution.',
            notification_type='assignment',
            related_grievance_id=grievance.id,
            is_read=False,
        )
        
        db.session.commit()

        if department_corrected:
            correction_details = {
                'grievance_id': grievance.id,
                'predicted_department': grievance.predicted_department,
                'old_assigned_department': previous_assigned_department,
                'new_assigned_department': officer.department,
                'prediction_confidence': grievance.prediction_confidence,
                'assigned_officer_id': officer.id,
            }
            from backend.services.audit_service import log_audit
            import json
            log_audit(user.id, 'correct_department_prediction', 'grievance', grievance.id, json.dumps(correction_details))
        
        # Send email notification to officer
        EmailService.send_officer_assignment_notification(
            officer_email=officer.office_email or officer.email,
            officer_name=officer.name,
            grievance_id=grievance.id,
            complaint_text=grievance.complaint_text,
            department=grievance.assigned_department,
            user_name=citizen.name,
            user_phone=citizen.phone
        )
        
        # Send email notification to citizen
        EmailService.send_status_update_notification(
            user_email=citizen.email,
            user_name=citizen.name,
            grievance_id=grievance.id,
            old_status=old_status,
            new_status='Assigned to Department',
            update_message=f'Your complaint has been assigned to {officer.name} ({officer.designation or "Officer"}) for resolution.',
            department=grievance.assigned_department,
            officer_name=officer.name
        )
        
        return jsonify({
            'message': 'Officer assigned successfully',
            'grievance': grievance.to_dict(include_officer=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """
    Get notifications for the current user
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        # Get unread count
        unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        
        # Get all notifications (limit to last 50)
        notifications = Notification.query.filter_by(user_id=user.id)\
            .order_by(Notification.created_at.desc())\
            .limit(50)\
            .all()
        
        return jsonify({
            'unread_count': unread_count,
            'notifications': [n.to_dict() for n in notifications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/notifications/<int:notification_id>/mark-read', methods=['PUT'])
def mark_notification_read(notification_id):
    """
    Mark a notification as read
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        if notification.user_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/retrain-model', methods=['POST'])
def trigger_retrain():
    """
    Trigger ML model retraining (Admin only).
    Retrains on data/indian_grievance_dataset.csv and reloads the classifier.
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        success, message = retrain_model(trigger='manual')
        if success:
            status = get_retrain_status()
            return jsonify({
                'message': message,
                'metadata': status
            }), 200
        return jsonify({'error': message}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/reset-lockout/<email>', methods=['POST'])
def reset_login_lockout(email):
    """Reset login lockout for an email (Admin only)."""
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        from backend.models import FailedLoginAttempt
        attempt = FailedLoginAttempt.query.filter_by(identifier=email).first()
        if attempt:
            attempt.attempt_count = 0
            attempt.lockout_until = None
            db.session.commit()
        
        return jsonify({'message': f'Lockout reset for {email}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/model-status', methods=['GET'])
def get_model_status():
    """
    Get current ML model training metadata (Admin only).
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        status = get_retrain_status()
        corrections = DepartmentCorrectionLog.query.order_by(DepartmentCorrectionLog.created_at.desc()).limit(20).all()
        total_corrections = DepartmentCorrectionLog.query.count()

        latest_training = status.get('latest_training') or {}
        metrics = latest_training.get('metrics', {})
        accuracy = metrics.get('accuracy')
        quality_note = None

        if accuracy is None:
            quality_note = (
                'Training metadata is unavailable. Run /api/admin/retrain-model to refresh metrics.'
            )
        elif accuracy < 0.75:
            quality_note = (
                'Current ML accuracy is below the recommended 75% threshold. '
                'Low-confidence cases are routed to manual review.'
            )
        else:
            quality_note = 'Model quality is acceptable for confidence-aware auto-routing.'

        status['correction_loop'] = {
            'total_corrections': total_corrections,
            'recent_corrections': [entry.to_dict() for entry in corrections],
        }
        status['quality_assessment'] = {
            'accuracy': accuracy,
            'recommended_minimum_accuracy': 0.75,
            'note': quality_note,
        }

        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/notifications/mark-all-read', methods=['PUT'])
def mark_all_notifications_read():
    """
    Mark all notifications as read for current user
    """
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        
        return jsonify({'message': 'All notifications marked as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/unsuspend-user/<int:user_id>', methods=['POST'])
def unsuspend_user(user_id):
    """
    Unsuspend a user account (Admin only)
    Required: admin_notes (for audit trail)
    """
    try:
        admin_user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response

        data = request.get_json() or {}
        admin_notes = data.get('admin_notes', '')
        if not admin_notes or len(admin_notes.strip()) < 10:
            return jsonify({'error': 'Detailed admin_notes is required (min 10 characters) for audit trail'}), 400

        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        if not target_user.account_suspended:
            return jsonify({'error': 'User is not suspended'}), 400

        # Unsuspend
        target_user.account_suspended = False
        previous_reason = target_user.suspension_reason
        target_user.suspension_reason = None

        # Optionally reset fraud warnings
        reset_warnings = data.get('reset_warnings', False)
        old_warnings = target_user.fraud_warnings
        if reset_warnings:
            target_user.fraud_warnings = 0

        db.session.commit()

        # Notify citizen
        NotificationService.queue_notification(
            user_id=target_user.id,
            title='Account Reinstated',
            message=f'Your account has been reinstated by admin. You can now submit grievances again.',
            notification_type='account_reinstated',
            is_read=False,
        )

        from backend.services.audit_service import log_audit
        import json
        log_audit(
            admin_user.id,
            'unsuspend_user',
            'user',
            user_id,
            json.dumps({
                'admin_notes': admin_notes,
                'previous_reason': previous_reason,
                'warnings_reset': reset_warnings,
                'old_warnings': old_warnings,
            })
        )

        return jsonify({
            'message': f'User {target_user.name} has been unsuspended',
            'fraud_warnings': target_user.fraud_warnings,
            'account_suspended': target_user.account_suspended,
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/fraud-reports/<int:report_id>/review', methods=['POST'])
def review_fraud_report(report_id):
    """
    Review a fraud report (Admin only)
    Actions: verify, dismiss
    """
    try:
        admin_user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response

        data = request.get_json() or {}
        action = data.get('action')
        admin_notes = data.get('admin_notes', '')

        if action not in ['verify', 'dismiss']:
            return jsonify({'error': 'Invalid action. Must be verify or dismiss'}), 400

        report = FraudReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Fraud report not found'}), 404

        grievance = Grievance.query.get(report.grievance_id)
        if not grievance:
            return jsonify({'error': 'Associated grievance not found'}), 404

        report.status = 'Verified' if action == 'verify' else 'Dismissed'
        report.admin_notes = admin_notes
        report.reviewed_at = datetime.utcnow()

        if action == 'verify':
            grievance.status = 'Closed'
            message = f"Fraud verified by Admin. Grievance closed. Notes: {admin_notes}"
            
            # Optionally suspend user
            if data.get('suspend_user'):
                target_user = User.query.get(grievance.user_id)
                if target_user:
                    target_user.account_suspended = True
                    target_user.suspension_reason = f"Verified Fraud on Grievance #{grievance.id}: {admin_notes}"
        else:
            # Dismissed - restore to Assigned or previous
            grievance.status = 'Assigned to Department'
            message = f"Fraud report dismissed by Admin. Resuming investigations. Notes: {admin_notes}"

        # Create update entry
        update = GrievanceUpdate(
            grievance_id=grievance.id,
            status=grievance.status,
            message=message,
            updated_by_role='ADMIN',
            updated_by_name=admin_user.name
        )
        db.session.add(update)
        db.session.commit()

        return jsonify({
            'message': f'Fraud report {action}ed successfully',
            'report_status': report.status,
            'grievance_status': grievance.status
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
