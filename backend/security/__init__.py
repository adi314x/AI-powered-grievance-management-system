"""
Security Module
Comprehensive security features for the Smart Grievance System
"""

from .firewall import (
    SecurityFirewall,
    require_firewall,
    validate_request_data,
    SecurityLogger
)
from .headers import SecurityHeaders, configure_cors_security

__all__ = [
    'SecurityFirewall',
    'require_firewall',
    'validate_request_data',
    'SecurityLogger',
    'SecurityHeaders',
    'configure_cors_security'
]
