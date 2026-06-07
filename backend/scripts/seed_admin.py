"""Seed an admin user for the platform."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app.models import User, UserRole
from app.auth import get_password_hash

Base.metadata.create_all(bind=engine)


def seed_admin():
    db = SessionLocal()
    email = "admin@sleepanalytics.com"
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"Admin user already exists: {email}")
        db.close()
        return

    admin = User(
        email=email,
        hashed_password=get_password_hash("admin123456"),
        full_name="Platform Admin",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    print(f"Admin user created: {email} / admin123456")
    db.close()


if __name__ == "__main__":
    seed_admin()
