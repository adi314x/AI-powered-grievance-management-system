"""Workflow authorization helpers for grievances."""

from backend.utils.roles import ROLE_ADMIN, ROLE_CITIZEN, ROLE_OFFICER, canonical_role


def can_view_grievance(user, grievance):
    """
    Return (allowed, error_message) for grievance read visibility.
    """
    role = canonical_role(user.role)
    if role == ROLE_ADMIN:
        return True, None
    if role == ROLE_CITIZEN:
        if grievance.user_id != user.id:
            return False, "Unauthorized to view this grievance"
        return True, None
    if role == ROLE_OFFICER:
        if grievance.assigned_department != user.department:
            return False, "Unauthorized to view this grievance"
        return True, None
    return False, "Unauthorized"


def can_officer_act_on_grievance(officer, grievance, require_assignment=False):
    """
    Return (allowed, error_message) for officer write operations.
    """
    if canonical_role(officer.role) != ROLE_OFFICER:
        return False, "Only officers can perform this action"

    if grievance.assigned_department != officer.department:
        return False, "You can only act on grievances in your department"

    if grievance.assigned_officer_id and grievance.assigned_officer_id != officer.id:
        return False, "This grievance is currently assigned to another officer"

    if require_assignment and grievance.assigned_officer_id != officer.id:
        return False, "Only the assigned officer can perform this action"

    return True, None
