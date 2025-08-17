#!/usr/bin/env python3
"""
Database seeding script for AI Governance Dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.models.user import User, Organization
from app.models.project import Project, CostBudget
from app.core.auth import get_password_hash


def seed_database():
    """Seed the database with initial data"""
    db = SessionLocal()
    
    try:
        # Create organization
        org = Organization(
            name="Default Organization",
            domain="example.com"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        
        # Create admin user
        admin_user = User(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            is_superuser=True,
            role="admin",
            organization_id=org.id
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Create demo user
        demo_user = User(
            email="demo@example.com",
            username="demo",
            full_name="Demo User",
            hashed_password=get_password_hash("demo123"),
            role="developer",
            organization_id=org.id
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        
        # Create demo project
        demo_project = Project(
            name="Demo Project",
            description="A demo project for testing",
            organization_id=org.id,
            owner_id=demo_user.id
        )
        db.add(demo_project)
        db.commit()
        db.refresh(demo_project)
        
        # Create budget for demo project
        budget = CostBudget(
            project_id=demo_project.id,
            daily_limit=100.0,
            monthly_limit=1000.0
        )
        db.add(budget)
        db.commit()
        
        print("Database seeded successfully!")
        print(f"Admin user: admin@example.com / admin123")
        print(f"Demo user: demo@example.com / demo123")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Seeding database...")
    seed_database()
