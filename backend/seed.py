"""
Seed script to create initial admin user, sample officers for the 5 departments,
and required role hierarchy entries.
Run this after setup or migrations: python -m backend.seed
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.database import upgrade_database
from backend.models import User, RoleHierarchy, DepartmentMapping, Grievance
from backend.config import Config
from backend.extensions import db

def seed_database(run_migrations=True):
    """Create initial admin, sample officers for exactly 5 departments, and hierarchy configs."""
    app = create_app()
    
    with app.app_context():
        if run_migrations:
            print("🔄 Running pending DB migrations before seeding...")
            upgrade_database()
            print("✓ Migrations applied")

        print("=" * 60)
        print("Seeding Database (5 Core Departments)")
        print("=" * 60)
        
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@grievance.gov').first()
        
        if admin:
            print("✓ Admin user already exists")
        else:
            admin = User(
                name='System Administrator',
                email='admin@grievance.gov',
                phone='9999999999',
                role='ADMIN',
                email_verified=True,
                phone_verified=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Created admin user")
            print("  Email: admin@grievance.gov")
            print("  Password: admin123")
        db.session.commit()
        
        # Exactly five allowed departments
        departments = [
            'Roads and Public Works',
            'Water Supply',
            'Electricity',
            'Sanitation and Waste Management',
            'Education'
        ]
        
        office_locations = {
            'Roads and Public Works': 'Highway & Public Works Division, Block A, Chennai - 600001',
            'Water Supply': 'Municipal Water Works, Block B, 2nd Floor, Chennai - 600002',
            'Electricity': 'State Electricity Board Office, Tower C, Chennai - 600003',
            'Sanitation and Waste Management': 'Municipal Sanitation Complex, Ground Floor, Chennai - 600004',
            'Education': 'Department of Education, Administrative Complex, Chennai - 600005',
        }

        email_slugs = {
            'Roads and Public Works': 'roads',
            'Water Supply': 'watersupply',
            'Electricity': 'electricity',
            'Sanitation and Waste Management': 'sanitation',
            'Education': 'education',
        }
        
        for idx, dept in enumerate(departments):
            slug = email_slugs[dept]
            email = f"{slug}@grievance.gov"
            officer = User.query.filter_by(email=email).first()
            
            # Also check old email format if existed
            if not officer:
                alt_email = f"{dept.lower().replace(' ', '').replace('&','').replace('/','')[:20]}@grievance.gov"
                officer = User.query.filter_by(email=alt_email).first()
            
            if officer:
                officer.department = dept
                officer.office_number = officer.office_number or f"044-2567-{idx + 1:04d}"
                officer.office_email = email
                officer.office_location = office_locations.get(dept, 'Government Office, Chennai')
                officer.office_building = f"Block {chr(65 + idx)}"
                officer.designation = f"Senior {dept} Officer"
                officer.set_password('officer123')
                print(f"✓ Updated officer details for {dept} ({officer.email})")
            else:
                officer = User(
                    name=f"{dept} Officer",
                    email=email,
                    phone=f"98765{idx + 1:05d}",
                    role='OFFICER',
                    department=dept,
                    office_number=f"044-2567-{idx + 1:04d}",
                    office_email=email,
                    office_location=office_locations.get(dept, 'Government Office, Chennai'),
                    office_building=f"Block {chr(65 + idx)}",
                    designation=f"Senior {dept} Officer",
                    email_verified=True,
                    phone_verified=True
                )
                officer.set_password('officer123')
                db.session.add(officer)
                print(f"✓ Created officer for {dept}")
                print(f"  Email: {email}")
                print(f"  Password: officer123")
                print(f"  Office: {officer.office_number}")
        
        db.session.commit()

        # Remove legacy dummy officer accounts from the old 16-department schema
        legacy_emails = [
            'sanitationsolidwaste@grievance.gov', 'seweragedrainage@grievance.gov',
            'roadspotholes@grievance.gov', 'streetlights@grievance.gov',
            'traffic@grievance.gov', 'police@grievance.gov',
            'cybercrime@grievance.gov', 'publichealth@grievance.gov',
            'foodsafety@grievance.gov', 'landrevenue@grievance.gov',
            'rationcardpds@grievance.gov', 'rtotransport@grievance.gov',
            'telecomnetwork@grievance.gov', 'environment@grievance.gov'
        ]
        legacy_officers = User.query.filter(User.email.in_(legacy_emails)).all()
        for leg_off in legacy_officers:
            DepartmentMapping.query.filter_by(section_officer_id=leg_off.id).update({'section_officer_id': None})
            Grievance.query.filter_by(assigned_officer_id=leg_off.id).update({'assigned_officer_id': None})
            db.session.delete(leg_off)
        if legacy_officers:
            print(f"✓ Cleaned up {len(legacy_officers)} legacy dummy officer accounts")
        db.session.commit()

        # Seed RoleHierarchy SLA defaults for the 5 departments
        for dept in departments:
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
                print(f"✓ Initialized SLA hierarchy for {dept} (48h SLA)")

        # Seed default DepartmentMapping if missing / update to active officers
        admin_user = User.query.filter_by(role='ADMIN').first()
        for dept in departments:
            slug = email_slugs[dept]
            dept_officer = User.query.filter_by(email=f"{slug}@grievance.gov").first()
            mapping = DepartmentMapping.query.filter_by(department=dept).first()
            if not mapping:
                mapping = DepartmentMapping(
                    department=dept,
                    ward='All Wards',
                    district='Chennai',
                    state='Tamil Nadu',
                    section_officer_id=dept_officer.id if dept_officer else None,
                    department_head_id=admin_user.id if admin_user else None
                )
                db.session.add(mapping)
                print(f"✓ Initialized DepartmentMapping for {dept}")
            else:
                if dept_officer:
                    mapping.section_officer_id = dept_officer.id
                if admin_user:
                    mapping.department_head_id = admin_user.id

        # Create a sample citizen
        citizen_email = 'citizen@example.com'
        citizen = User.query.filter_by(email=citizen_email).first()
        
        if citizen:
            print("✓ Sample citizen already exists")
        else:
            citizen = User(
                name='John Doe',
                email=citizen_email,
                phone='9876543210',
                role='CITIZEN',
                email_verified=True,
                phone_verified=True
            )
            citizen.set_password('citizen123')
            db.session.add(citizen)
            print("✓ Created sample citizen")
            print(f"  Email: {citizen_email}")
            print(f"  Password: citizen123")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)
        print("\nLogin Credentials:")
        print("-" * 60)
        print("ADMIN:")
        print("  Email: admin@grievance.gov")
        print("  Password: admin123")
        print("\nOFFICERS (Five Departments):")
        print("  Roads and Public Works:          roads@grievance.gov / officer123")
        print("  Water Supply:                    watersupply@grievance.gov / officer123")
        print("  Electricity:                     electricity@grievance.gov / officer123")
        print("  Sanitation and Waste Management: sanitation@grievance.gov / officer123")
        print("  Education:                       education@grievance.gov / officer123")
        print("\nCITIZEN:")
        print("  Email: citizen@example.com")
        print("  Password: citizen123")
        print("=" * 60)

if __name__ == '__main__':
    seed_database()
