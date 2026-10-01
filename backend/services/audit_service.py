"""Audit Trail Service - Log all significant actions"""
from flask import request
from backend.models_addons import AuditLog
from backend.extensions import db


def log_audit(user_id, action, entity_type=None, entity_id=None, details=None):
    """Log an audit entry"""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string[:500] if request and request.user_agent else None
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Audit log failed: {e}")
