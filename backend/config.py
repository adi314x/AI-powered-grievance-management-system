import os
from datetime import timedelta

class Config:
    DEFAULT_SECRET_KEY = 'dev-secret-key-change-in-production'

    @classmethod
    def _env_bool(cls, key, default):
        val = os.environ.get(key, str(default)).lower()
        return val in ('true', '1', 't', 'y', 'yes')

    @classmethod
    def reload_from_env(cls):
        # Environment mode
        cls.ENVIRONMENT = os.environ.get('FLASK_ENV', os.environ.get('APP_ENV', 'development')).lower()
        cls.IS_PRODUCTION = cls.ENVIRONMENT == 'production'

        # Secret key for JWT
        cls.SECRET_KEY = os.environ.get('SECRET_KEY', cls.DEFAULT_SECRET_KEY)

        # Database (Render/Heroku use DATABASE_URL; fix postgres:// -> postgresql:// for SQLAlchemy)
        db_url = os.environ.get('DATABASE_URL', 'sqlite:///grievance.db')
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        cls.DATABASE_URL = db_url
        cls.SQLALCHEMY_DATABASE_URI = db_url
        cls.SQLALCHEMY_TRACK_MODIFICATIONS = False
        cls.AUTO_CREATE_TABLES = cls._env_bool('AUTO_CREATE_TABLES', 'false')

        # JWT
        cls.JWT_SECRET_KEY = cls.SECRET_KEY
        cls.JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
        cls.JWT_RESET_TOKEN_EXPIRES = timedelta(
            minutes=int(os.environ.get('JWT_RESET_TOKEN_EXPIRES_MINUTES', '15'))
        )
        cls.JWT_REFRESH_TOKEN_EXPIRES = timedelta(
            days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', '30'))
        )
        cls.ENABLE_REFRESH_TOKENS = cls._env_bool('ENABLE_REFRESH_TOKENS', 'true')

        # Canonical frontend/app URL used in email and notification links
        cls.APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:8000').rstrip('/')

        # OTP Settings
        cls.OTP_EXPIRY_MINUTES = 5
        cls.OTP_MAX_ATTEMPTS = 5
        cls.OTP_RATE_LIMIT_PER_HOUR = 3

        # Demo/Debug delivery toggles (disabled by default).
        cls.DEMO_EMAIL_MODE = cls._env_bool('DEMO_EMAIL_MODE', 'false')
        cls.DEMO_SMS_MODE = cls._env_bool('DEMO_SMS_MODE', 'false')

        # Email Configuration
        cls.MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        cls.MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
        cls.MAIL_USE_TLS = cls._env_bool('MAIL_USE_TLS', 'true')
        cls.MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
        cls.MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
        cls.MAIL_DEFAULT_SENDER = os.environ.get(
            'MAIL_DEFAULT_SENDER',
            'Smart Grievance System <noreply@grievance.gov>'
        )

        # ML Model paths
        project_root = os.path.dirname(os.path.dirname(__file__))
        cls.MODEL_PATH = os.path.join(project_root, 'ml', 'artifacts', 'model.joblib')
        cls.VECTORIZER_PATH = os.path.join(project_root, 'ml', 'artifacts', 'vectorizer.joblib')
        cls.MODEL_METADATA_PATH = os.path.join(project_root, 'ml', 'artifacts', 'train_metadata.json')
        cls.ENABLE_STARTUP_MODEL_LOAD = cls._env_bool('ENABLE_STARTUP_MODEL_LOAD', 'true')
        cls.ENABLE_SCHEDULER = cls._env_bool('ENABLE_SCHEDULER', 'true')
        cls.SCHEDULER_AUTOSTART = cls._env_bool('SCHEDULER_AUTOSTART', 'false')
        cls.ENABLE_SCHEDULED_RETRAIN = cls._env_bool('ENABLE_SCHEDULED_RETRAIN', 'true')
        cls.ML_AUTO_ASSIGN_CONFIDENCE_THRESHOLD = float(
            os.environ.get('ML_AUTO_ASSIGN_CONFIDENCE_THRESHOLD', '0.65')
        )
        cls.ML_MANUAL_REVIEW_DEPARTMENT = os.environ.get(
            'ML_MANUAL_REVIEW_DEPARTMENT',
            'Manual Review Queue'
        )

        # Authoritative Five Allowed Departments
        cls.ALLOWED_DEPARTMENTS = [
            'Roads and Public Works',
            'Water Supply',
            'Electricity',
            'Sanitation and Waste Management',
            'Education'
        ]
        cls.DEFAULT_DEPARTMENT = 'Roads and Public Works'

        # Optional extra CORS origins (comma-separated, e.g. "https://user.github.io,https://myfrontend.com")
        cls.CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '')

        # App settings
        cls.PORT = int(os.environ.get('PORT', 8000))

    @classmethod
    def validate_runtime_config(cls):
        if cls.IS_PRODUCTION and cls.SECRET_KEY == cls.DEFAULT_SECRET_KEY:
            raise RuntimeError('SECRET_KEY must be set in production')
        if cls.IS_PRODUCTION and cls.DEMO_EMAIL_MODE:
            raise RuntimeError('DEMO_EMAIL_MODE must be false in production')

        warnings = []
        if cls.IS_PRODUCTION and cls.APP_BASE_URL.startswith('http://localhost'):
            warnings.append('APP_BASE_URL still points to localhost in production')
        if cls.IS_PRODUCTION and cls.DEMO_SMS_MODE:
            warnings.append('DEMO_SMS_MODE=true: phone OTP delivery is in demo mode and not production-grade')
        has_smtp = bool(cls.MAIL_USERNAME and cls.MAIL_PASSWORD)
        has_formspree = bool(os.environ.get('FORMSPREE_ENDPOINT', '').strip())
        if cls.IS_PRODUCTION and not cls.DEMO_EMAIL_MODE and not has_smtp and not has_formspree:
            warnings.append('No production email provider configured (SMTP or FORMSPREE_ENDPOINT)')
        return warnings


Config.reload_from_env()
