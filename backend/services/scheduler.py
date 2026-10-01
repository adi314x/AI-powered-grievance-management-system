"""
Background Scheduler for periodic tasks
- Comment escalation checks: every hour
- SLA breach scan: every hour
- ML model retraining: every 7 days (configurable)
"""
import os
import threading
import time
from datetime import datetime
from backend.config import Config
from backend.services.comment_escalation import check_and_escalate_comments
from backend.services.model_retrain import retrain_model

# Retrain every N hours (168 = 7 days). Set RETRAIN_INTERVAL_HOURS=24 for daily.
RETRAIN_INTERVAL_HOURS = int(os.environ.get('RETRAIN_INTERVAL_HOURS', '168'))


def scan_sla_breaches(app=None):
    """
    Scan for grievances that have passed their SLA deadline
    and mark them as breached. Returns count of newly breached grievances.
    """
    if app:
        with app.app_context():
            return _execute_sla_scan()
    return _execute_sla_scan()

def _execute_sla_scan():
    from backend.extensions import db
    from backend.models import Grievance, User
    from backend.services.notification_service import NotificationService
    from backend.utils.roles import ADMIN_ROLE_VALUES

    now = datetime.utcnow()
    terminal_statuses = ('Resolved', 'Closed')

    overdue = Grievance.query.filter(
        Grievance.sla_deadline.isnot(None),
        Grievance.sla_deadline < now,
        Grievance.sla_breached.is_(False),
        ~Grievance.status.in_(terminal_statuses),
    ).all()

    if not overdue:
        return 0

    breached_count = 0
    for grievance in overdue:
        grievance.sla_breached = True
        grievance.sla_breached_at = now
        breached_count += 1

        # Notify assigned officer
        if grievance.assigned_officer_id:
            NotificationService.queue_notification(
                user_id=grievance.assigned_officer_id,
                title=f'⏰ SLA Breached - Grievance #{grievance.id}',
                message=(
                    f'SLA deadline of {grievance.sla_hours}h has been exceeded. '
                    f'Please take immediate action.'
                ),
                notification_type='sla_breach',
                related_grievance_id=grievance.id,
                is_read=False,
            )

        # Notify admins
        admins = User.query.filter(User.role.in_(ADMIN_ROLE_VALUES)).all()
        for admin in admins:
            NotificationService.queue_notification(
                user_id=admin.id,
                title=f'⏰ SLA Breached - Grievance #{grievance.id}',
                message=(
                    f'Grievance #{grievance.id} has exceeded its {grievance.sla_hours}h SLA. '
                    f'Department: {grievance.assigned_department}'
                ),
                notification_type='sla_breach',
                related_grievance_id=grievance.id,
                is_read=False,
            )

    try:
        db.session.commit()
    except Exception as db_error:
        db.session.rollback()
        print(f"❌ Failed to persist SLA breach updates: {db_error}")
        return 0

    return breached_count


class BackgroundScheduler:
    """Simple background scheduler for running periodic tasks"""
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        self._hours_since_retrain = 0
    
    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
    
    def start(self):
        """Start the background scheduler"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        retrain_status = "enabled" if Config.ENABLE_SCHEDULED_RETRAIN else "disabled"
        print(
            "✓ Background scheduler started - "
            "comment escalations + SLA scan every hour, "
            f"scheduled retrain {retrain_status} (interval={RETRAIN_INTERVAL_HOURS}h)"
        )
    
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run_scheduler(self):
        """Main scheduler loop - runs every hour"""
        while self.running:
            try:
                # Wait for 1 hour (3600 seconds)
                time.sleep(3600)
                
                if not self.running:
                    break
                
                if not self.app:
                    continue
                
                with self.app.app_context():
                    # Comment escalation (every hour)
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running comment escalation check...")
                    escalated_count = check_and_escalate_comments()
                    if escalated_count > 0:
                        print(f"✓ Escalated {escalated_count} overdue comments")
                    else:
                        print("✓ No comments need escalation")

                    # SLA breach scan (every hour)
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running SLA breach scan...")
                    breached_count = scan_sla_breaches()
                    if breached_count > 0:
                        print(f"✓ Marked {breached_count} grievances as SLA-breached")
                    else:
                        print("✓ No new SLA breaches")
                    
                    # Model retraining (every RETRAIN_INTERVAL_HOURS)
                    self._hours_since_retrain += 1
                    if Config.ENABLE_SCHEDULED_RETRAIN and self._hours_since_retrain >= RETRAIN_INTERVAL_HOURS:
                        self._hours_since_retrain = 0
                        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled ML model retraining...")
                        success, msg = retrain_model(trigger='scheduler')
                        if success:
                            print(f"✓ {msg}")
                        else:
                            print(f"❌ Retrain failed: {msg}")
                
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                continue

    def get_runtime_status(self):
        """Expose scheduler runtime state for health and diagnostics."""
        return {
            'enabled': Config.ENABLE_SCHEDULER,
            'autostart': Config.SCHEDULER_AUTOSTART,
            'running': self.running,
            'thread_alive': bool(self.thread and self.thread.is_alive()),
            'app_bound': self.app is not None,
            'scheduled_retrain_enabled': Config.ENABLE_SCHEDULED_RETRAIN,
            'retrain_interval_hours': RETRAIN_INTERVAL_HOURS,
        }

# Global scheduler instance
scheduler = BackgroundScheduler()

