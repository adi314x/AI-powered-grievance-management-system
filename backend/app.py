from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables from .env file
load_dotenv()

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.config import Config
from backend.extensions import db, migrate
from backend import models
from backend.models_addons import AuditLog, GrievanceRating
from backend.routes.auth import auth_bp
from backend.routes.grievances import grievances_bp
from backend.routes.admin import admin_bp
from backend.routes.addons import addons_bp
from backend.routes.rag import rag_bp
from backend.services.classifier import classifier
from backend.services.scheduler import scheduler
from backend.security import SecurityHeaders, configure_cors_security

def _is_flask_db_command():
    """Detect Flask-Migrate CLI context to avoid runtime side effects."""
    argv = [arg.lower() for arg in sys.argv]
    return 'flask' in (argv[0] if argv else '') and 'db' in argv


def create_app():
    Config.reload_from_env()
    config_warnings = Config.validate_runtime_config()

    app = Flask(__name__, static_folder='../frontend')
    app.config.from_object(Config)

    for warning in config_warnings:
        print(f"[WARN] Config warning: {warning}")
    
    # Initialize security headers
    SecurityHeaders(app)
    
    # Enable CORS with security
    configure_cors_security(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    
    # Initialize scheduler
    scheduler.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(grievances_bp, url_prefix='/api/grievances')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(addons_bp, url_prefix='/api')
    app.register_blueprint(rag_bp, url_prefix='/api/rag')
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/health')
    def health():
        db_status = {
            'connected': False,
            'dialect': None,
            'error': None,
        }
        try:
            db.session.execute(text('SELECT 1'))
            db_status['connected'] = True
            db_status['dialect'] = db.engine.dialect.name
        except Exception as exc:
            db_status['error'] = str(exc)

        model_status = classifier.get_runtime_status()
        scheduler_status = scheduler.get_runtime_status()

        status = 'healthy'
        status_code = 200
        if not db_status['connected']:
            status = 'degraded'
            status_code = 503
        elif app.config.get('ENABLE_STARTUP_MODEL_LOAD') and not model_status.get('model_loaded'):
            status = 'degraded'

        return {
            'status': status,
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'environment': app.config.get('ENVIRONMENT'),
            'app_base_url': app.config.get('APP_BASE_URL'),
            'demo_email_mode': app.config.get('DEMO_EMAIL_MODE'),
            'demo_sms_mode': app.config.get('DEMO_SMS_MODE'),
            'database': db_status,
            'ml': {
                'model_loaded': model_status.get('model_loaded'),
                'loaded_at_utc': model_status.get('loaded_at_utc'),
            },
            'scheduler': scheduler_status,
        }, status_code
    
    @app.route('/<path:path>')
    def serve_static(path):
        filepath = os.path.join(app.static_folder, path)
        if os.path.exists(filepath):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')
    
    # Runtime startup tasks (schema bootstrap via migrations, not create_all).
    with app.app_context():
        if app.config['AUTO_CREATE_TABLES']:
            db.create_all()
            print("⚠ AUTO_CREATE_TABLES enabled: created tables without migrations")
        
        # Load ML classifier
        if app.config['ENABLE_STARTUP_MODEL_LOAD']:
            classifier.load_model()
        
        print("[SECURITY] Security Firewall: ENABLED")
        print("   - Rate Limiting: Active")
        print("   - Input Validation: Active")
        print("   - XSS Protection: Active")
        print("   - SQL Injection Prevention: Active")
        print("   - IP Blocking: Active")
        
        should_start_scheduler = (
            app.config['ENABLE_SCHEDULER']
            and app.config.get('SCHEDULER_AUTOSTART', False)
            and not _is_flask_db_command()
            and not app.testing
        )
        if should_start_scheduler:
            scheduler.start()
        elif app.config['ENABLE_SCHEDULER'] and not app.testing:
            print("[INFO] Scheduler autostart is disabled. Set SCHEDULER_AUTOSTART=true on exactly one process to run background jobs.")
        
        if os.getenv('FLASK_ENV', 'development') == 'development':
            from backend.security.firewall import blocked_ips
            blocked_ips.difference_update(('127.0.0.1', 'localhost', '::1'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = Config.PORT
    is_production = Config.ENVIRONMENT == 'production'
    
    print(f"\n{'='*60}")
    print(f"🚀 Smart Grievance System Starting...")
    print(f"📍 Running on http://localhost:{port}")
    print(f"📧 Email Console Mode: {Config.DEMO_EMAIL_MODE}")
    print(f"🔧 Environment: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=not is_production)
