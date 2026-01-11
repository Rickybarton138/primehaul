#!/usr/bin/env python3
"""
Initialize database tables for PrimeHaul
Run this once to create all tables in the correct order
"""
import os
import sys
from sqlalchemy import create_engine
from app.models import Base

def init_database():
    """Create all database tables"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    print(f"🔗 Connecting to database...")
    engine = create_engine(database_url)

    print("📦 Creating all tables...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database initialized successfully!")
    print("🎉 All tables created!")

if __name__ == "__main__":
    init_database()
