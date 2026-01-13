#!/usr/bin/env python3
"""
🚀 QUICK RESET - One command to reset everything and test

Usage:
    python3 QUICK_RESET.py              # Reset LOCAL database
    python3 QUICK_RESET.py --railway    # Reset RAILWAY database
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.models import Base, Company, PricingConfig, User
from app.auth import hash_password
import uuid
from datetime import datetime, timedelta, timezone

def get_database_url(use_railway=False):
    """Get the correct database URL"""
    if use_railway:
        # Use Railway database
        url = os.getenv("DATABASE_URL")
        if not url:
            print("❌ ERROR: DATABASE_URL not set")
            print("💡 Get it from: Railway dashboard → Postgres → Connect")
            sys.exit(1)
        return url
    else:
        # Use local database
        return "sqlite:///./primehaul_local.db"

def quick_reset(use_railway=False):
    """Reset database and create test data"""

    database_url = get_database_url(use_railway)

    print("=" * 70)
    print("🚀 QUICK RESET")
    print("=" * 70)
    print("")

    if use_railway:
        print("🌐 Resetting RAILWAY database...")
        print("⚠️  This will delete all production data!")
        print("")
        confirm = input("Type 'YES' to continue: ")
        if confirm != "YES":
            print("❌ Cancelled")
            sys.exit(0)
    else:
        print("💻 Resetting LOCAL database...")

    print("")
    print("🔗 Connecting...")
    engine = create_engine(database_url)

    print("🗑️  Dropping tables...")
    # Use raw SQL to drop with CASCADE (handles circular dependencies)
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        conn.commit()

    print("📦 Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("🎨 Creating test data...")

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Create company
        company = Company(
            id=uuid.uuid4(),
            company_name='PrimeHaul Removals',
            slug='test-removals-ltd',
            email='hello@primehaul.co.uk',
            phone='+44 20 1234 5678',
            subscription_status='active',
            is_active=True,
            primary_color='#ffffff',
            secondary_color='#000000',
            created_at=datetime.now(timezone.utc),
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(company)
        db.flush()

        # Create pricing
        pricing = PricingConfig(
            id=uuid.uuid4(),
            company_id=company.id,
            price_per_cbm=35.00,
            callout_fee=250.00,
            bulky_item_fee=25.00,
            fragile_item_fee=15.00,
            price_per_km=2.00,
            base_distance_km=0,
            price_per_floor=15.00,
            no_lift_surcharge=50.00,
            parking_street_fee=25.00,
            parking_permit_fee=40.00,
            parking_limited_fee=60.00,
            parking_distance_per_50m=10.00,
            narrow_access_fee=35.00,
            time_restriction_fee=25.00,
            booking_required_fee=20.00,
            outdoor_steps_per_5=15.00,
            outdoor_path_fee=20.00,
            weight_threshold_kg=1000,
            price_per_kg_over_threshold=0.50,
            pack1_price=1.05,
            pack2_price=1.55,
            pack3_price=2.00,
            pack6_price=1.05,
            robe_carton_price=10.00,
            tape_price=1.14,
            paper_price=7.50,
            mattress_cover_price=1.74
        )
        db.add(pricing)

        # Create admin
        admin = User(
            id=uuid.uuid4(),
            company_id=company.id,
            email='admin@test.com',
            password_hash=hash_password('test123'),
            full_name='Test Admin',
            role='owner',
            is_active=True
        )
        db.add(admin)

        db.commit()

        print("")
        print("=" * 70)
        print("✅ RESET COMPLETE!")
        print("=" * 70)
        print("")

        if use_railway:
            base_url = "https://primehaul-production.up.railway.app"
        else:
            base_url = "http://localhost:8000"

        print("📱 CUSTOMER QUOTE URL (test this on your phone):")
        print(f"   {base_url}/s/test-removals-ltd/test-123/start-v2")
        print("")
        print("🎯 ADMIN DASHBOARD:")
        print(f"   {base_url}/test-removals-ltd/admin/dashboard")
        print("")
        print("🔑 LOGIN:")
        print("   Email:    admin@test.com")
        print("   Password: test123")
        print("")
        print("=" * 70)
        print("")
        print("🧪 QUICK TEST CHECKLIST:")
        print("   1. Open customer URL on your phone")
        print("   2. Go through the flow (2-3 minutes)")
        print("   3. Check quote appears in admin dashboard")
        print("   4. Verify monochrome design (white buttons, no emojis)")
        print("")
        print("✨ Ready for demo!")
        print("")

    except Exception as e:
        db.rollback()
        print(f"❌ ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    use_railway = "--railway" in sys.argv or "-r" in sys.argv
    quick_reset(use_railway)
