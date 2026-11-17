"""Shared aggregation helpers for grievance reporting."""

from sqlalchemy import func

from backend.extensions import db
from backend.models import Grievance, GrievanceUpdate


RESOLUTION_STATUSES = ('Resolved', 'Closed')


def resolution_timestamp_subquery():
    """Return the latest Resolved/Closed update timestamp per grievance."""
    return (
        db.session.query(
            GrievanceUpdate.grievance_id.label('grievance_id'),
            func.max(GrievanceUpdate.timestamp).label('resolved_at'),
        )
        .filter(GrievanceUpdate.status.in_(RESOLUTION_STATUSES))
        .group_by(GrievanceUpdate.grievance_id)
        .subquery()
    )


def resolution_timestamp_expression(subquery):
    """Use the resolution update timestamp, falling back to updated_at."""
    return func.coalesce(subquery.c.resolved_at, Grievance.updated_at)
