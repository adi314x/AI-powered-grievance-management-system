#!/usr/bin/env python3
"""
Smart Grievance System - Application Entry Point
"""

from backend.app import create_app
from backend.config import Config
import os

if __name__ == '__main__':
    app = create_app()
    port = Config.PORT
    
    print("\n" + "="*70)
    print("🚀 Smart Grievance System - Starting Server")
    print("="*70)
    print(f"📍 URL: http://localhost:{port}")
    print(f"🔒 Security: Enabled")
    print(f"📧 Email Mode: {'Demo (Console)' if app.config['DEMO_EMAIL_MODE'] else 'Production (SMTP)'}")
    print("="*70 + "\n")
    
    is_production = os.getenv('FLASK_ENV', 'development') == 'production'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=not is_production,
        use_reloader=False
    )
