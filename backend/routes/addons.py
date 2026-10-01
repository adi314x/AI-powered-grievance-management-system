"""Add-on routes: Public dashboard, Ratings, Audit, Export, QR"""
from flask import Blueprint, jsonify, request, send_file
from datetime import datetime, timedelta
from io import BytesIO
import json
import qrcode
from sqlalchemy import func
from backend.models import Grievance, User
from backend.models_addons import AuditLog, GrievanceRating
from backend.extensions import db
from backend.services.audit_service import log_audit
from backend.services.email_service import EmailService
from backend.routes.auth import get_current_user_from_token
from backend.utils.roles import canonical_role

addons_bp = Blueprint('addons', __name__)


def _anonymize_public_location(raw_location):
    """Return a coarse, privacy-safe location label for public cards."""
    if not raw_location:
        return "Location withheld"

    location = raw_location.strip()
    if not location:
        return "Location withheld"

    if "lat:" in location.lower() or "long:" in location.lower():
        return "GPS area"

    parts = [part.strip() for part in location.split(",") if part.strip()]
    if len(parts) >= 2:
        return ", ".join(parts[-2:])
    return parts[0]


def _summarize_complaint_for_public(text, max_len=160):
    if not text:
        return "A grievance was resolved by the department."
    clean_text = " ".join(text.split())
    if len(clean_text) <= max_len:
        return clean_text
    return f"{clean_text[:max_len - 3].rstrip()}..."


@addons_bp.route('/public/stats', methods=['GET'])
def public_stats():
    """Public dashboard - aggregated stats (no auth required)"""
    try:
        total = Grievance.query.count()
        resolved = Grievance.query.filter(Grievance.status.in_(['Resolved', 'Closed'])).count()
        pending = total - resolved
        dept_counts = db.session.query(
            Grievance.assigned_department,
            func.count(Grievance.id)
        ).group_by(Grievance.assigned_department).all()
        by_dept_map = {d: 0 for d in Config.ALLOWED_DEPARTMENTS}
        for d, c in dept_counts:
            if d in by_dept_map:
                by_dept_map[d] = c
            elif d == Config.ML_MANUAL_REVIEW_DEPARTMENT and c > 0:
                by_dept_map[d] = c
        
        # Avg resolution time (days) for resolved grievances
        resolved_grievances = Grievance.query.filter(
            Grievance.status.in_(['Resolved', 'Closed']),
            Grievance.created_at.isnot(None),
            Grievance.updated_at.isnot(None)
        ).all()
        total_days = sum((g.updated_at - g.created_at).total_seconds() / 86400 for g in resolved_grievances)
        avg_resolution_days = round(total_days / len(resolved_grievances), 1) if resolved_grievances else 0
        
        return jsonify({
            'total_grievances': total,
            'resolved': resolved,
            'pending': pending,
            'resolution_rate': round(resolved / total * 100, 1) if total else 0,
            'avg_resolution_days': avg_resolution_days,
            'by_department': by_dept_map,
            'updated_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@addons_bp.route('/public/resolved-cases', methods=['GET'])
def public_resolved_cases():
    """Public anonymized feed of recently resolved grievances."""
    try:
        try:
            limit = int(request.args.get('limit', 6))
        except (TypeError, ValueError):
            limit = 6
        limit = max(1, min(limit, 12))

        grievances = Grievance.query.filter(
            Grievance.status.in_(['Resolved', 'Closed'])
        ).order_by(
            Grievance.updated_at.desc(),
            Grievance.id.desc()
        ).limit(limit).all()

        cases = []
        for grievance in grievances:
            department = grievance.assigned_department or 'General'
            cases.append({
                'id': grievance.id,
                'title': f'{department} grievance resolved',
                'description': _summarize_complaint_for_public(grievance.complaint_text),
                'department': department,
                'location': _anonymize_public_location(grievance.location),
                'status': grievance.status,
                'resolved_at': grievance.updated_at.isoformat() if grievance.updated_at else None,
            })

        return jsonify({
            'cases': cases,
            'count': len(cases),
            'updated_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@addons_bp.route('/grievances/<int:grievance_id>/rate', methods=['POST'])
def submit_rating(grievance_id):
    """Submit rating for resolved grievance"""
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        data = request.get_json()
        rating = data.get('rating', 0)
        feedback_text = data.get('feedback_text', '')
        
        if not 1 <= rating <= 5:
            return jsonify({'error': 'Rating must be 1-5'}), 400
        
        grievance = Grievance.query.get(grievance_id)
        if not grievance:
            return jsonify({'error': 'Grievance not found'}), 404
        if grievance.user_id != user.id:
            return jsonify({'error': 'Can only rate your own grievances'}), 403
        if grievance.status not in ['Resolved', 'Closed']:
            return jsonify({'error': 'Can only rate resolved grievances'}), 400
        
        existing = GrievanceRating.query.filter_by(grievance_id=grievance_id, user_id=user.id).first()
        if existing:
            existing.rating = rating
            existing.feedback_text = feedback_text
            existing.resolution_speed = data.get('resolution_speed')
            existing.officer_helpfulness = data.get('officer_helpfulness')
        else:
            r = GrievanceRating(
                grievance_id=grievance_id,
                user_id=user.id,
                rating=rating,
                feedback_text=feedback_text,
                resolution_speed=data.get('resolution_speed'),
                officer_helpfulness=data.get('officer_helpfulness')
            )
            db.session.add(r)
        
        db.session.commit()
        log_audit(user.id, 'rate_grievance', 'grievance', grievance_id, json.dumps({'rating': rating}))
        return jsonify({'message': 'Thank you for your feedback!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@addons_bp.route('/grievances/<int:grievance_id>/rating', methods=['GET'])
def get_rating(grievance_id):
    """Get rating for a grievance"""
    try:
        user, auth_response = get_current_user_from_token(return_error=True)
        if auth_response:
            return auth_response
        
        r = GrievanceRating.query.filter_by(grievance_id=grievance_id, user_id=user.id).first()
        if not r:
            return jsonify({'rating': None}), 200
        return jsonify(r.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@addons_bp.route('/grievances/<int:grievance_id>/qr', methods=['GET'])
def get_qr_code(grievance_id):
    """Generate QR code for grievance tracking"""
    try:
        grievance = Grievance.query.get(grievance_id)
        if not grievance:
            return jsonify({'error': 'Not found'}), 404
        
        track_url = EmailService.tracking_url(grievance_id)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(track_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1e40af", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@addons_bp.route('/admin/audit/export', methods=['GET'])
def export_audit():
    """Export audit log (Admin only)"""
    try:
        user, auth_response = get_current_user_from_token(return_error=True, required_roles=['ADMIN'])
        if auth_response:
            return auth_response
        
        days = int(request.args.get('days', 7))
        since = datetime.utcnow() - timedelta(days=days)
        logs = AuditLog.query.filter(AuditLog.created_at >= since).order_by(AuditLog.created_at.desc()).limit(5000).all()
        
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            
            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph("Audit Log Report", styles['Title']))
            elements.append(Paragraph(f"Period: Last {days} days", styles['Normal']))
            
            data = [['Time', 'User ID', 'Action', 'Entity', 'IP']]
            for log in logs:
                data.append([
                    log.created_at.strftime('%Y-%m-%d %H:%M') if log.created_at else '',
                    str(log.user_id or ''),
                    log.action or '',
                    f"{log.entity_type or ''}#{log.entity_id or ''}",
                    log.ip_address or ''
                ])
            
            t = Table(data)
            t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke)]))
            elements.append(t)
            doc.build(elements)
            buf.seek(0)
            return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=f'audit_log_{days}days.pdf')
        except ImportError:
            return jsonify({'logs': [l.to_dict() for l in logs]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@addons_bp.route('/admin/export/grievances', methods=['GET'])
def export_grievances():
    """Export grievances to Excel (Admin/Officer)"""
    try:
        user, auth_response = get_current_user_from_token(
            return_error=True,
            required_roles=['ADMIN', 'OFFICER']
        )
        if auth_response:
            return auth_response
        
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Grievances"
        ws.append(['ID', 'Department', 'Status', 'Location', 'Created', 'Updated'])
        
        if canonical_role(user.role) == 'ADMIN':
            grievances = Grievance.query.order_by(Grievance.created_at.desc()).limit(1000).all()
        else:
            grievances = Grievance.query.filter_by(assigned_department=user.department).order_by(Grievance.created_at.desc()).limit(500).all()
        
        for g in grievances:
            ws.append([g.id, g.assigned_department, g.status, g.location or '', 
                      g.created_at.strftime('%Y-%m-%d') if g.created_at else '',
                      g.updated_at.strftime('%Y-%m-%d') if g.updated_at else ''])
        
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        log_audit(user.id, 'export_grievances', details=json.dumps({'count': len(grievances)}))
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name=f'grievances_export_{datetime.now().strftime("%Y%m%d")}.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
