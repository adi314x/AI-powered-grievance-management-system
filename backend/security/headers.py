"""
Security Headers Middleware
Adds security headers to all responses
"""

from flask import make_response

class SecurityHeaders:
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security headers for Flask app"""
        
        @app.after_request
        def add_security_headers(response):
            """Add security headers to every response"""
            
            # Prevent clickjacking
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            
            # Prevent MIME type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Enable XSS protection
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Strict Transport Security (HTTPS only)
            # Commented out for local development, enable in production
            # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Content Security Policy
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://unpkg.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "img-src 'self' data: blob: https:; "
                "connect-src 'self' https: http: https://nominatim.openstreetmap.org; "
                "frame-ancestors 'self';"
            )
            
            # Referrer Policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions Policy (formerly Feature Policy)
            response.headers['Permissions-Policy'] = (
                "geolocation=(self), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            )
            
            # Remove server header to hide Flask version
            response.headers.pop('Server', None)
            
            # Add custom security header
            response.headers['X-Powered-By'] = 'Smart Grievance System'
            
            return response
        
        return app


def configure_cors_security(app):
    """
    Configure CORS with security in mind.
    In production, allow APP_BASE_URL and CORS_ALLOWED_ORIGINS if specified.
    In development, allow all origins for convenience.
    """
    from flask_cors import CORS
    import os

    is_production = os.getenv('FLASK_ENV') == 'production'
    app_base_url = os.getenv('APP_BASE_URL', '').rstrip('/')
    cors_env = os.getenv('CORS_ALLOWED_ORIGINS', '').strip()

    allowed_origins = []
    if cors_env:
        for origin in cors_env.split(','):
            origin_clean = origin.strip().rstrip('/')
            if origin_clean:
                allowed_origins.append(origin_clean)

    if app_base_url and app_base_url not in allowed_origins:
        allowed_origins.append(app_base_url)

    if not allowed_origins or not is_production:
        allowed_origins = "*"

    CORS(app, 
         resources={
             r"/*": {
                 "origins": allowed_origins,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"],
                 "expose_headers": ["X-RateLimit-Remaining", "X-RateLimit-Limit"],
                 "max_age": 3600,
                 "supports_credentials": True
             }
         })
