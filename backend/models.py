from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db
from backend.utils.roles import canonical_role

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='CITIZEN')  # Active roles: CITIZEN, OFFICER, ADMIN (legacy officer aliases still accepted)
    role_level = db.Column(db.Integer, default=0)  # Legacy hierarchy field; retained for compatibility
    department = db.Column(db.String(100), nullable=True)  # For officers
    
    # Jurisdiction fields
    ward = db.Column(db.String(50), nullable=True)  # Ward/Area
    district = db.Column(db.String(100), nullable=True)  # District
    # Note: 'state' column is defined once below under legacy/residential fields
    jurisdiction_type = db.Column(db.String(20), nullable=True)  # 'ward', 'district', 'state'
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    aadhaar_last4 = db.Column(db.String(4), nullable=True)
    aadhaar_hash = db.Column(db.String(255), nullable=True)
    
    # Officer-specific fields
    office_number = db.Column(db.String(50), nullable=True)  # Office contact number
    office_email = db.Column(db.String(120), nullable=True)  # Official office email
    office_location = db.Column(db.String(500), nullable=True)  # Office address
    office_building = db.Column(db.String(200), nullable=True)  # Building/Block name
    designation = db.Column(db.String(100), nullable=True)  # Officer designation
    
    # Profile fields
    profile_photo = db.Column(db.Text, nullable=True)  # Base64 encoded image
    
    # Residential Address (User's permanent address as per Aadhaar)
    residential_address = db.Column(db.Text, nullable=True)  # Full residential address
    residential_city = db.Column(db.String(100), nullable=True)
    residential_state = db.Column(db.String(100), nullable=True)
    residential_pincode = db.Column(db.String(10), nullable=True)
    
    # Address fields (used for profile + jurisdiction state)
    address = db.Column(db.String(500), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)  # Serves both jurisdiction and residential legacy
    pincode = db.Column(db.String(10), nullable=True)
    
    date_of_birth = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    
    # Fraud tracking
    fraud_warnings = db.Column(db.Integer, default=0)  # Number of fraud warnings
    account_suspended = db.Column(db.Boolean, default=False)  # Account suspension status
    suspension_reason = db.Column(db.Text, nullable=True)  # Reason for suspension
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    grievances = db.relationship('Grievance', backref='user', lazy=True, foreign_keys='Grievance.user_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': canonical_role(self.role),
            'department': self.department,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'office_number': self.office_number,
            'office_email': self.office_email,
            'office_location': self.office_location,
            'office_building': self.office_building,
            'designation': self.designation,
            'profile_photo': self.profile_photo,
            # Residential Address (Permanent)
            'residential_address': self.residential_address,
            'residential_city': self.residential_city,
            'residential_state': self.residential_state,
            'residential_pincode': self.residential_pincode,
            # Legacy fields (backward compatibility)
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'aadhaar_last4': self.aadhaar_last4,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FailedLoginAttempt(db.Model):
    __tablename__ = 'failed_login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(120), nullable=False, index=True)
    attempt_count = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OTPRequest(db.Model):
    __tablename__ = 'otp_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(120), nullable=False, index=True)  # email or phone
    otp_hash = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(10), nullable=False)  # 'email' or 'phone'
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_otp(self, otp):
        self.otp_hash = generate_password_hash(str(otp), method='pbkdf2:sha256')
    
    def check_otp(self, otp):
        return check_password_hash(self.otp_hash, str(otp))


class Grievance(db.Model):
    __tablename__ = 'grievances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    complaint_text = db.Column(db.Text, nullable=False)
    predicted_department = db.Column(db.String(100), nullable=False)
    assigned_department = db.Column(db.String(100), nullable=False)
    prediction_confidence = db.Column(db.Float, default=0.0)
    prediction_source = db.Column(db.String(30), default='ml')
    requires_manual_triage = db.Column(db.Boolean, default=False)
    triage_reason = db.Column(db.Text, nullable=True)
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Current officer handling the case
    current_role_level = db.Column(db.Integer, default=2)  # Legacy hierarchy field; active workflow uses assigned officer/admin escalation
    escalation_level = db.Column(db.Integer, default=0)  # Number of times escalated
    status = db.Column(db.String(50), nullable=False, default='Received')
    
    # Jurisdiction fields
    ward = db.Column(db.String(50), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    
    # SLA tracking
    sla_hours = db.Column(db.Integer, default=48)  # Default 48 hours
    sla_deadline = db.Column(db.DateTime, nullable=True)
    sla_breached = db.Column(db.Boolean, default=False)
    sla_breached_at = db.Column(db.DateTime, nullable=True)  # When SLA was first breached
    last_action_at = db.Column(db.DateTime, default=datetime.utcnow)  # Last update time
    location = db.Column(db.Text, nullable=True)  # Changed to Text for longer addresses
    images = db.Column(db.Text, nullable=True)  # JSON array of base64 images
    
    # Complainant information (captured at time of complaint)
    complainant_dob = db.Column(db.String(20), nullable=True)  # Date of birth
    complainant_gender = db.Column(db.String(50), nullable=True)  # Gender
    
    # Content moderation fields
    is_flagged = db.Column(db.Boolean, default=False)
    moderation_score = db.Column(db.Integer, default=0)
    moderation_severity = db.Column(db.String(20), nullable=True)
    moderation_flags = db.Column(db.Text, nullable=True)  # JSON string
    
    # AI image detection fields
    ai_image_detected = db.Column(db.Boolean, default=False)
    ai_detection_confidence = db.Column(db.Float, default=0.0)
    ai_detection_details = db.Column(db.Text, nullable=True)  # JSON string
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    updates = db.relationship('GrievanceUpdate', backref='grievance', lazy=True, order_by='GrievanceUpdate.timestamp')
    comments = db.relationship('GrievanceComment', backref='grievance', lazy=True, order_by='GrievanceComment.created_at')
    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id], backref='assigned_grievances')
    
    @property
    def department(self):
        return self.assigned_department or self.predicted_department

    def to_dict(self, include_updates=False, include_comments=False, include_officer=False):
        import json
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'complaint_text': self.complaint_text,
            'department': self.assigned_department or self.predicted_department,
            'predicted_department': self.predicted_department,
            'assigned_department': self.assigned_department,
            'prediction_confidence': self.prediction_confidence,
            'prediction_source': self.prediction_source,
            'requires_manual_triage': self.requires_manual_triage,
            'triage_reason': self.triage_reason,
            'assigned_officer_id': self.assigned_officer_id,
            'status': self.status or 'Received',
            'location': self.location,
            'images': json.loads(self.images) if self.images else [],
            'complainant_dob': self.complainant_dob,
            'complainant_gender': self.complainant_gender,
            'is_flagged': self.is_flagged,
            'moderation_score': self.moderation_score,
            'moderation_severity': self.moderation_severity,
            'ai_image_detected': self.ai_image_detected,
            'ai_detection_confidence': self.ai_detection_confidence,
            'ai_detection_details': json.loads(self.ai_detection_details) if self.ai_detection_details else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Add complainant information from User table
        complainant = User.query.get(self.user_id)
        if complainant:
            result['complainant_name'] = complainant.name
            result['complainant_phone'] = complainant.phone
            result['complainant_email'] = complainant.email
        
        # Always include comment count
        result['comment_count'] = len(self.comments) if self.comments else 0
        
        if include_officer and self.assigned_officer:
            result['assigned_officer'] = {
                'id': self.assigned_officer.id,
                'name': self.assigned_officer.name,
                'email': self.assigned_officer.email,
                'phone': self.assigned_officer.phone,
                'office_number': self.assigned_officer.office_number,
                'office_email': self.assigned_officer.office_email,
                'office_location': self.assigned_officer.office_location,
                'office_building': self.assigned_officer.office_building,
                'designation': self.assigned_officer.designation,
                'department': self.assigned_officer.department
            }
        if include_updates:
            result['updates'] = [update.to_dict() for update in self.updates]
        if include_comments:
            result['comments'] = [comment.to_dict() for comment in self.comments]
        return result


class GrievanceUpdate(db.Model):
    __tablename__ = 'grievance_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    updated_by_role = db.Column(db.String(20), nullable=False)  # SYSTEM, OFFICER, ADMIN
    updated_by_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notify_sent = db.Column(db.Boolean, default=False)
    notify_sent_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grievance_id': self.grievance_id,
            'status': self.status,
            'message': self.message,
            'updated_by_role': self.updated_by_role,
            'updated_by_name': self.updated_by_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'notify_sent': self.notify_sent,
        }


class GrievanceComment(db.Model):
    __tablename__ = 'grievance_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    user_role = db.Column(db.String(20), nullable=False)  # CITIZEN, OFFICER, ADMIN
    user_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notification tracking for escalation
    notified_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Officer who was notified
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    response_deadline = db.Column(db.DateTime, nullable=True)  # When to escalate if no response
    escalated = db.Column(db.Boolean, default=False)
    escalated_at = db.Column(db.DateTime, nullable=True)
    escalated_to_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='comments', foreign_keys=[user_id])
    notified_officer = db.relationship('User', foreign_keys=[notified_officer_id])
    escalated_to_officer = db.relationship('User', foreign_keys=[escalated_to_officer_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'grievance_id': self.grievance_id,
            'user_id': self.user_id,
            'comment_text': self.comment_text,
            'user_role': self.user_role,
            'user_name': self.user_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'notified_officer_id': self.notified_officer_id,
            'escalated': self.escalated,
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'assignment', 'status_update', 'comment', etc.
    related_grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications', foreign_keys=[user_id])
    related_grievance = db.relationship('Grievance', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'related_grievance_id': self.related_grievance_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class FraudReport(db.Model):
    __tablename__ = 'fraud_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=False)
    reported_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    complainant_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fraud_type = db.Column(db.String(50), nullable=False)  # 'false_complaint', 'fake_images', 'wrong_location', 'exaggerated'
    description = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.Text, nullable=True)  # JSON with evidence details
    site_visit_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending')  # Pending, Verified, Dismissed
    action_taken = db.Column(db.String(100), nullable=True)  # Warning, Penalty, Account_Suspended, etc.
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    grievance = db.relationship('Grievance', backref='fraud_reports')
    reporting_officer = db.relationship('User', foreign_keys=[reported_by_officer_id], backref='fraud_reports_filed')
    complainant = db.relationship('User', foreign_keys=[complainant_user_id], backref='fraud_reports_received')
    
    def to_dict(self):
        return {
            'id': self.id,
            'grievance_id': self.grievance_id,
            'reported_by_officer_id': self.reported_by_officer_id,
            'complainant_user_id': self.complainant_user_id,
            'fraud_type': self.fraud_type,
            'description': self.description,
            'evidence': self.evidence,
            'site_visit_notes': self.site_visit_notes,
            'status': self.status,
            'action_taken': self.action_taken,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }

class RoleHierarchy(db.Model):
    __tablename__ = 'role_hierarchy'
    
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    role_name = db.Column(db.String(100), nullable=False)  # e.g., "Junior Engineer", "Line Man"
    role_level = db.Column(db.Integer, nullable=False)  # 1-5
    parent_level = db.Column(db.Integer, nullable=True)  # Parent role level
    sla_hours = db.Column(db.Integer, default=48)  # SLA for this level
    can_assign_to_field = db.Column(db.Boolean, default=False)  # Can assign to field officers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'department': self.department,
            'role_name': self.role_name,
            'role_level': self.role_level,
            'parent_level': self.parent_level,
            'sla_hours': self.sla_hours,
            'can_assign_to_field': self.can_assign_to_field
        }

class DepartmentMapping(db.Model):
    __tablename__ = 'department_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    ward = db.Column(db.String(50), nullable=True)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    section_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Default Section Officer
    department_head_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Department Head
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    section_officer = db.relationship('User', foreign_keys=[section_officer_id])
    department_head = db.relationship('User', foreign_keys=[department_head_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'department': self.department,
            'ward': self.ward,
            'district': self.district,
            'state': self.state,
            'section_officer_id': self.section_officer_id,
            'department_head_id': self.department_head_id
        }

class EscalationLog(db.Model):
    __tablename__ = 'escalation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(db.Integer, db.ForeignKey('grievances.id'), nullable=False)
    from_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    to_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_role_level = db.Column(db.Integer, nullable=False)
    to_role_level = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)  # 'SLA Breach', 'Manual Escalation', 'Complexity'
    escalation_type = db.Column(db.String(50), default='auto')  # 'auto', 'manual'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    grievance = db.relationship('Grievance', backref='escalation_logs')
    from_officer = db.relationship('User', foreign_keys=[from_officer_id])
    to_officer = db.relationship('User', foreign_keys=[to_officer_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'grievance_id': self.grievance_id,
            'from_officer_id': self.from_officer_id,
            'to_officer_id': self.to_officer_id,
            'from_role_level': self.from_role_level,
            'to_role_level': self.to_role_level,
            'reason': self.reason,
            'escalation_type': self.escalation_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
