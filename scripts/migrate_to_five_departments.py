"""
Safe Migration & Remapping Script for 5 Core Departments
Supports SQLite and PostgreSQL.
Usage:
    python scripts/migrate_to_five_departments.py [--backup]
"""

import os
import sys
import shutil
import argparse
from datetime import datetime

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

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

from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models import Grievance, User, RoleHierarchy, DepartmentMapping
from backend.models_addons import DepartmentCorrectionLog

DEPARTMENT_REMAPPING = {
    # Direct / slight name variations
    'Roads & Potholes': 'Roads and Public Works',
    'Roads and Public Works': 'Roads and Public Works',
    'Roads': 'Roads and Public Works',
    'Traffic': 'Roads and Public Works',
    'RTO / Transport': 'Roads and Public Works',
    'Police': 'Roads and Public Works',
    'Cyber Crime': 'Roads and Public Works',
    'Land & Revenue': 'Roads and Public Works',

    'Water Supply': 'Water Supply',
    'Water': 'Water Supply',

    'Electricity': 'Electricity',
    'Streetlights': 'Electricity',
    'Telecom / Network': 'Electricity',

    'Sanitation & Solid Waste': 'Sanitation and Waste Management',
    'Sanitation and Waste Management': 'Sanitation and Waste Management',
    'Sanitation': 'Sanitation and Waste Management',
    'Sewerage & Drainage': 'Sanitation and Waste Management',
    'Public Health': 'Sanitation and Waste Management',
    'Environment': 'Sanitation and Waste Management',
    'Food Safety': 'Sanitation and Waste Management',
    'Ration Card / PDS': 'Sanitation and Waste Management',

    'Education': 'Education',
}

FIVE_DEPARTMENTS = [
    'Roads and Public Works',
    'Water Supply',
    'Electricity',
    'Sanitation and Waste Management',
    'Education'
]


def backup_database(app):
    """Create a backup of the database before running migration."""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.join(PROJECT_ROOT, db_path)
        
        if os.path.exists(db_path):
            backup_path = f"{db_path}.backup_{timestamp}"
            shutil.copy2(db_path, backup_path)
            print(f"✓ SQLite database backed up to: {backup_path}")
            return backup_path
        else:
            print(f"ℹ SQLite DB file does not exist yet at {db_path}; backup skipped.")
            return None
    elif 'postgresql' in db_uri or 'postgres' in db_uri:
        print("ℹ PostgreSQL detected.")
        print(f"  To take a manual backup before running on production, run:")
        print(f"  pg_dump \"$DATABASE_URL\" > backup_{timestamp}.sql")
        return None
    return None


def run_department_migration(make_backup=True):
    """Safely remap existing complaints and officers to the 5 allowed departments."""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Safe Department Remapping to 5 Core Departments")
        print("=" * 60)

        if make_backup:
            backup_database(app)

        # 1. Remap Grievances
        print("\n[1/4] Checking and remapping Grievance records...")
        grievances = Grievance.query.all()
        remap_count = 0

        for g in grievances:
            updated = False
            # Check assigned_department
            if g.assigned_department and g.assigned_department != Config.ML_MANUAL_REVIEW_DEPARTMENT:
                if g.assigned_department not in FIVE_DEPARTMENTS:
                    new_dept = DEPARTMENT_REMAPPING.get(g.assigned_department, Config.DEFAULT_DEPARTMENT)
                    print(f"  Grievance #{g.id}: remapping assigned '{g.assigned_department}' -> '{new_dept}'")
                    g.assigned_department = new_dept
                    updated = True

            # Check predicted_department
            if g.predicted_department and g.predicted_department not in FIVE_DEPARTMENTS:
                new_pred = DEPARTMENT_REMAPPING.get(g.predicted_department, Config.DEFAULT_DEPARTMENT)
                g.predicted_department = new_pred
                updated = True

            if updated:
                remap_count += 1

        print(f"✓ Processed {len(grievances)} grievances; remapped {remap_count} records.")

        # 2. Remap Officers
        print("\n[2/4] Checking and remapping Officer departments...")
        officers = User.query.filter(User.role.in_(['OFFICER', 'officer'])).all()
        officer_remap_count = 0

        for off in officers:
            if off.department and off.department not in FIVE_DEPARTMENTS:
                new_dept = DEPARTMENT_REMAPPING.get(off.department, Config.DEFAULT_DEPARTMENT)
                print(f"  Officer #{off.id} ({off.email}): remapping '{off.department}' -> '{new_dept}'")
                off.department = new_dept
                officer_remap_count += 1

        print(f"✓ Processed {len(officers)} officers; remapped {officer_remap_count} records.")

        # 3. Ensure RoleHierarchy for 5 Departments
        print("\n[3/4] Ensuring RoleHierarchy entries for 5 departments...")
        for dept in FIVE_DEPARTMENTS:
            hierarchy = RoleHierarchy.query.filter_by(department=dept).first()
            if not hierarchy:
                hierarchy = RoleHierarchy(
                    department=dept,
                    role_name=f"{dept} Section Officer",
                    role_level=2,
                    parent_level=1,
                    sla_hours=48,
                    can_assign_to_field=True
                )
                db.session.add(hierarchy)
                print(f"  + Added RoleHierarchy for '{dept}' (48h SLA)")
            else:
                print(f"  ✓ RoleHierarchy already exists for '{dept}'")

        # 4. Ensure DepartmentMapping for 5 Departments
        print("\n[4/4] Ensuring DepartmentMapping entries for 5 departments...")
        admin_user = User.query.filter_by(role='ADMIN').first()
        for dept in FIVE_DEPARTMENTS:
            mapping = DepartmentMapping.query.filter_by(department=dept).first()
            if not mapping:
                officer = User.query.filter_by(department=dept, role='OFFICER').first()
                mapping = DepartmentMapping(
                    department=dept,
                    ward='All Wards',
                    district='Chennai',
                    state='Tamil Nadu',
                    section_officer_id=officer.id if officer else None,
                    department_head_id=admin_user.id if admin_user else None
                )
                db.session.add(mapping)
                print(f"  + Added DepartmentMapping for '{dept}'")
            else:
                print(f"  ✓ DepartmentMapping already exists for '{dept}'")

        db.session.commit()
        print("\n" + "=" * 60)
        print("✓ Database migration & remapping completed successfully!")
        print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Safely remap grievance departments to 5 core departments.")
    parser.add_argument('--no-backup', action='store_true', help="Skip database backup step.")
    args = parser.parse_args()

    run_department_migration(make_backup=not args.no_backup)
