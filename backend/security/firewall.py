"""
Security Firewall System
Protects user information and prevents attacks
"""

from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
import re
import bleach
from email_validator import validate_email, EmailNotValidError

# Suspicious activity tracking
suspicious_ips = {}
blocked_ips = set()

# Rate limiting tracking
request_counts = {}

class SecurityFirewall:
    """
    Comprehensive security firewall for the application
    """
    
    # Blocked patterns for non-SQL payload classes.
    GENERIC_BLOCKED_PATTERNS = [
        r'(<script|<iframe|<object|<embed|javascript:)',  # XSS
        r'(\.\.\/|\.\.\\)',  # Path traversal
        r'(\b(?:exec|eval|system|shell_exec)\s*\()',  # Code injection function calls
    ]

    # SQLi patterns focus on statement/operator context to avoid false positives
    # for ordinary user text (e.g. "please provide an update").
    SQL_INJECTION_PATTERNS = [
        r'\bunion(?:\s+all)?\s+select\b',
        r'\bselect\s+[\w\*,\s]+\s+from\b',
        r'\binsert\s+into\b',
        r'\bdelete\s+from\b',
        r'\bdrop\s+table\b',
        r'\balter\s+table\b',
        r'\bcreate\s+table\b',
        r'\bupdate\s+[a-zA-Z_][a-zA-Z0-9_]*\s+set\b',
        r'(?:\'|"|`)\s*(?:or|and)\s+(?:\'[^\']*\'|"[^"]*"|`[^`]*`|\d+)\s*=\s*(?:\'[^\']*\'|"[^"]*"|`[^`]*`|\d+)',
        r';\s*(?:select|insert|update|delete|drop|alter|create|union)\b',
        r'\b(?:information_schema|xp_cmdshell|pg_sleep|sleep\s*\(|benchmark\s*\(|waitfor\s+delay|load_file\s*\(|into\s+outfile)\b',
    ]
    
    # Allowed HTML tags for sanitization
    ALLOWED_TAGS = ['b', 'i', 'u', 'strong', 'em', 'p', 'br']

    @staticmethod
    def _contains_sql_injection(text):
        """Detect SQLi-style payloads without blocking normal conversational text."""
        for pattern in SecurityFirewall.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def check_ip_blocked(ip_address):
        """Check if IP is blocked (localhost never blocked in development)"""
        import os
        if os.getenv('FLASK_ENV', 'development') == 'development' and ip_address:
            first = (ip_address or '').split(',')[0].strip()
            if first in ('127.0.0.1', 'localhost', '::1'):
                return False
        return ip_address in blocked_ips
    
    @staticmethod
    def block_ip(ip_address, reason="Suspicious activity"):
        """Block an IP address"""
        blocked_ips.add(ip_address)
        print(f"🚫 BLOCKED IP: {ip_address} - Reason: {reason}")
    
    @staticmethod
    def track_suspicious_activity(ip_address, reason):
        """Track suspicious activity from an IP"""
        if ip_address not in suspicious_ips:
            suspicious_ips[ip_address] = []
        
        suspicious_ips[ip_address].append({
            'reason': reason,
            'timestamp': datetime.utcnow()
        })
        
        # Block if more than 5 suspicious activities in 1 hour
        recent_activities = [
            a for a in suspicious_ips[ip_address]
            if datetime.utcnow() - a['timestamp'] < timedelta(hours=1)
        ]
        
        if len(recent_activities) >= 5:
            SecurityFirewall.block_ip(ip_address, f"Multiple suspicious activities: {reason}")
            return True
        
        return False
    
    @staticmethod
    def validate_input(text, field_name="input"):
        """
        Validate and sanitize input text
        Returns: (is_valid, sanitized_text, error_message)
        """
        if not text:
            return True, "", None
        
        # Check for blocked non-SQL patterns.
        for pattern in SecurityFirewall.GENERIC_BLOCKED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, None, f"Invalid {field_name}: Contains prohibited content"

        if SecurityFirewall._contains_sql_injection(text):
            return False, None, f"Invalid {field_name}: Contains prohibited content"
        
        # Sanitize HTML
        sanitized = bleach.clean(
            text,
            tags=SecurityFirewall.ALLOWED_TAGS,
            strip=True
        )
        
        return True, sanitized, None
    
    @staticmethod
    def validate_email_address(email):
        """
        Validate email address
        Returns: (is_valid, normalized_email, error_message)
        """
        try:
            validated = validate_email(email, check_deliverability=False)
            return True, validated.normalized, None
        except EmailNotValidError as e:
            return False, None, str(e)
    
    @staticmethod
    def validate_phone(phone):
        """
        Validate phone number (Indian format)
        Returns: (is_valid, error_message)
        """
        # Remove spaces and special characters
        phone_clean = re.sub(r'[^\d+]', '', phone)
        
        # Check Indian phone format
        if re.match(r'^(\+91)?[6-9]\d{9}$', phone_clean):
            return True, None
        
        return False, "Invalid phone number format"
    
    @staticmethod
    def check_password_strength(password):
        """
        Check password strength
        Returns: (is_strong, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'admin123', 'qwerty123']
        if password.lower() in weak_passwords:
            return False, "Password is too common. Please choose a stronger password"
        
        return True, None
    
    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filename to prevent directory traversal
        """
        # Remove path components
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Only allow alphanumeric, dash, underscore, and dot
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        return filename
    
    @staticmethod
    def check_rate_limit(ip_address, endpoint, max_requests=10, window_minutes=1):
        """
        Check rate limit for an IP on a specific endpoint
        Returns: (is_allowed, remaining_requests)
        """
        key = f"{ip_address}:{endpoint}"
        now = datetime.utcnow()
        
        if key not in request_counts:
            request_counts[key] = []
        
        # Remove old requests outside the window
        request_counts[key] = [
            req_time for req_time in request_counts[key]
            if now - req_time < timedelta(minutes=window_minutes)
        ]
        
        # Check if limit exceeded
        if len(request_counts[key]) >= max_requests:
            return False, 0
        
        # Add current request
        request_counts[key].append(now)
        
        remaining = max_requests - len(request_counts[key])
        return True, remaining


def _bypass_firewall_in_dev():
    """In development, bypass firewall entirely for easier testing"""
    import os
    return os.getenv('FLASK_ENV', 'development') != 'production'


def _is_trusted_ip(ip_address):
    """Bypass firewall for localhost in development"""
    import os
    if os.getenv('FLASK_ENV', 'development') == 'development':
        if not ip_address:
            return True
        first_ip = (ip_address or '').split(',')[0].strip()
        if first_ip in ('127.0.0.1', 'localhost', '::1'):
            return True
        if first_ip.startswith('::ffff:127.') or first_ip.startswith('127.'):
            return True
    return False


def require_firewall(max_requests=10, window_minutes=1):
    """
    Decorator to apply firewall protection to routes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In development, skip firewall for easier local testing
            if _bypass_firewall_in_dev():
                return f(*args, **kwargs)
            
            # Get client IP
            ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
            
            # Bypass for trusted IPs
            if _is_trusted_ip(ip_address):
                return f(*args, **kwargs)
            
            # Check if IP is blocked
            if SecurityFirewall.check_ip_blocked(ip_address):
                return jsonify({
                    'error': 'Access Denied',
                    'message': 'Your IP has been blocked due to suspicious activity'
                }), 403
            
            # Check rate limit
            endpoint = request.endpoint or 'unknown'
            is_allowed, remaining = SecurityFirewall.check_rate_limit(
                ip_address, endpoint, max_requests, window_minutes
            )
            
            if not is_allowed:
                SecurityFirewall.track_suspicious_activity(ip_address, "Rate limit exceeded")
                return jsonify({
                    'error': 'Too Many Requests',
                    'message': 'Rate limit exceeded. Please try again later.'
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response_obj, status_code = response[0], response[1]
            else:
                response_obj, status_code = response, 200
            
            # Add security headers
            if hasattr(response_obj, 'headers'):
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Limit'] = str(max_requests)
            
            return response_obj, status_code
        
        return decorated_function
    return decorator


def validate_request_data(required_fields=None, optional_fields=None):
    """
    Decorator to validate and sanitize request data
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Check required fields
            if required_fields:
                for field in required_fields:
                    if field not in data:
                        return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Validate and sanitize all text fields
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    is_valid, sanitized, error = SecurityFirewall.validate_input(value, key)
                    if not is_valid:
                        ip_address = request.remote_addr
                        SecurityFirewall.track_suspicious_activity(ip_address, f"Invalid input in {key}")
                        return jsonify({'error': error}), 400
                    sanitized_data[key] = sanitized
                else:
                    sanitized_data[key] = value
            
            # Replace request data with sanitized version
            request.sanitized_data = sanitized_data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


class SecurityLogger:
    """
    Log security events
    """
    
    @staticmethod
    def log_event(event_type, ip_address, details):
        """Log a security event"""
        timestamp = datetime.utcnow().isoformat()
        print(f"🔒 SECURITY [{timestamp}] {event_type} from {ip_address}: {details}")
    
    @staticmethod
    def log_blocked_attempt(ip_address, reason):
        """Log a blocked attempt"""
        SecurityLogger.log_event("BLOCKED", ip_address, reason)
    
    @staticmethod
    def log_suspicious_activity(ip_address, activity):
        """Log suspicious activity"""
        SecurityLogger.log_event("SUSPICIOUS", ip_address, activity)
    
    @staticmethod
    def log_authentication_failure(ip_address, email):
        """Log failed authentication"""
        SecurityLogger.log_event("AUTH_FAILURE", ip_address, f"Failed login for {email}")
