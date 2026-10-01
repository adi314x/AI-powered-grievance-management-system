"""Centralized in-app notification helpers."""

from backend.extensions import db
from backend.models import Notification


class NotificationService:
    @staticmethod
    def queue_notification(user_id, title, message, notification_type, related_grievance_id=None, is_read=False):
        """Create an in-app notification in the current DB transaction."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_grievance_id=related_grievance_id,
            is_read=is_read,
        )
        db.session.add(notification)
        return notification
