"""Canonical role helpers for workflow authorization."""

ROLE_CITIZEN = "CITIZEN"
ROLE_OFFICER = "OFFICER"
ROLE_ADMIN = "ADMIN"

CANONICAL_ROLES = {ROLE_CITIZEN, ROLE_OFFICER, ROLE_ADMIN}

# Legacy role names from older hierarchy experiments map to active workflow roles.
LEGACY_ROLE_ALIASES = {
    "FIELD_OFFICER": ROLE_OFFICER,
    "SECTION_OFFICER": ROLE_OFFICER,
    "DEPARTMENT_HEAD": ROLE_OFFICER,
    "DISTRICT_HEAD": ROLE_OFFICER,
    "STATE_HEAD": ROLE_OFFICER,
}
OFFICER_ROLE_VALUES = (ROLE_OFFICER,) + tuple(LEGACY_ROLE_ALIASES.keys())
ADMIN_ROLE_VALUES = (ROLE_ADMIN,)

ROLE_LEVELS = {
    ROLE_CITIZEN: 0,
    ROLE_OFFICER: 1,
    ROLE_ADMIN: 2,
}


def canonical_role(role):
    """Map stored role values to the active workflow role set."""
    normalized = (role or "").strip().upper()
    if normalized in CANONICAL_ROLES:
        return normalized
    return LEGACY_ROLE_ALIASES.get(normalized, normalized)


def is_role(user_or_role, expected_role):
    """Check role match using canonical roles."""
    role = user_or_role.role if hasattr(user_or_role, "role") else user_or_role
    return canonical_role(role) == canonical_role(expected_role)


def has_any_role(user_or_role, allowed_roles):
    """Check whether role belongs to an allowed set after canonicalization."""
    role = user_or_role.role if hasattr(user_or_role, "role") else user_or_role
    normalized_allowed = {canonical_role(value) for value in allowed_roles}
    return canonical_role(role) in normalized_allowed


def role_level_for_log(user_or_role):
    """Return a small canonical level value for escalation logging."""
    role = user_or_role.role if hasattr(user_or_role, "role") else user_or_role
    return ROLE_LEVELS.get(canonical_role(role), 0)
