"""
Seed script to populate database with sample data.
Run this script to insert sample donors, hospitals, and requests.

Usage:
    python seed.py
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine, Base
from app.models.models import Donor, Hospital, Request, UrgencyLevel, RequestStatus
from app.services.db_utils import init_db
from app.services.cache import sync_all_donors_to_cache

# Sample data
SAMPLE_DONORS = [
    {
        "name": "Aryan Kumar",
        "blood_group": "A+",
        "lat": 28.545,
        "lng": 77.273,
        "available": True,
        "last_donation_date": datetime.now() - timedelta(days=45),
    },
    {
        "name": "Simran Singh",
        "blood_group": "B+",
        "lat": 28.554,
        "lng": 77.265,
        "available": True,
        "last_donation_date": datetime.now() - timedelta(days=30),
    },
    {
        "name": "Priya Sharma",
        "blood_group": "O+",
        "lat": 28.535,
        "lng": 77.280,
        "available": True,
        "last_donation_date": datetime.now() - timedelta(days=60),
    },
    {
        "name": "Rahul Verma",
        "blood_group": "AB+",
        "lat": 28.550,
        "lng": 77.270,
        "available": False,
        "last_donation_date": datetime.now() - timedelta(days=15),
    },
    {
        "name": "Anjali Patel",
        "blood_group": "A-",
        "lat": 28.560,
        "lng": 77.275,
        "available": True,
        "last_donation_date": None,
    },
    {
        "name": "Vikram Reddy",
        "blood_group": "B-",
        "lat": 28.540,
        "lng": 77.285,
        "available": True,
        "last_donation_date": datetime.now() - timedelta(days=90),
    },
    {
        "name": "Neha Gupta",
        "blood_group": "O-",
        "lat": 28.525,
        "lng": 77.290,
        "available": True,
        "last_donation_date": datetime.now() - timedelta(days=120),
    },
    {
        "name": "Karan Malhotra",
        "blood_group": "AB-",
        "lat": 28.555,
        "lng": 77.260,
        "available": True,
        "last_donation_date": datetime.now() - timedelta(days=75),
    },
]

SAMPLE_HOSPITALS = [
    {"name": "Apollo Hospital", "location": "Delhi", "lat": 28.545, "lng": 77.273},
    {"name": "AIIMS", "location": "Delhi", "lat": 28.554, "lng": 77.265},
    {"name": "Max Hospital", "location": "Delhi", "lat": 28.535, "lng": 77.280},
    {"name": "Fortis Hospital", "location": "Delhi", "lat": 28.550, "lng": 77.270},
    {"name": "Safdarjung Hospital", "location": "Delhi", "lat": 28.560, "lng": 77.275},
    {"name": "BLK Hospital", "location": "Delhi", "lat": 28.540, "lng": 77.285},
]

SAMPLE_REQUESTS = [
    {
        "hospital_id": 1,  # Apollo Hospital
        "blood_type": "O+",
        "urgency": UrgencyLevel.CRITICAL,
        "status": RequestStatus.PENDING,
    },
    {
        "hospital_id": 2,  # AIIMS
        "blood_type": "A+",
        "urgency": UrgencyLevel.HIGH,
        "status": RequestStatus.ACTIVE,
    },
    {
        "hospital_id": 3,  # Max Hospital
        "blood_type": "B+",
        "urgency": UrgencyLevel.MEDIUM,
        "status": RequestStatus.PENDING,
    },
    {
        "hospital_id": 4,  # Fortis Hospital
        "blood_type": "AB-",
        "urgency": UrgencyLevel.HIGH,
        "status": RequestStatus.PENDING,
    },
    {
        "hospital_id": 5,  # Safdarjung Hospital
        "blood_type": "O-",
        "urgency": UrgencyLevel.CRITICAL,
        "status": RequestStatus.PENDING,
    },
    {
        "hospital_id": 6,  # BLK Hospital
        "blood_type": "B-",
        "urgency": UrgencyLevel.LOW,
        "status": RequestStatus.PENDING,
    },
]


def seed_database():
    """Seed the database with sample data"""
    db: Session = SessionLocal()
    
    try:
        # Initialize database tables
        print("📦 Initializing database tables...")
        init_db()
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("🗑️  Clearing existing data...")
        db.query(Request).delete()
        db.query(Donor).delete()
        db.query(Hospital).delete()
        db.commit()
        
        # Insert hospitals
        print("🏥 Inserting hospitals...")
        hospitals = []
        for hospital_data in SAMPLE_HOSPITALS:
            hospital = Hospital(**hospital_data)
            db.add(hospital)
            hospitals.append(hospital)
        db.commit()
        
        # Refresh to get IDs
        for hospital in hospitals:
            db.refresh(hospital)
        
        print(f"✅ Created {len(hospitals)} hospitals")
        
        # Insert donors
        print("👥 Inserting donors...")
        donors = []
        for donor_data in SAMPLE_DONORS:
            donor = Donor(**donor_data)
            db.add(donor)
            donors.append(donor)
        db.commit()
        
        # Refresh to get IDs
        for donor in donors:
            db.refresh(donor)
        
        print(f"✅ Created {len(donors)} donors")
        
        # Sync donors to Redis cache + GEO index
        print("🔄 Syncing donors to Redis cache and GEO index...")
        try:
            from app.services.cache import set_donor_availability
            from app.services.geo import upsert_donor_geo
            for donor in donors:
                asyncio.run(set_donor_availability(donor.id, donor.available))
                asyncio.run(upsert_donor_geo(donor.id, donor.lat, donor.lng))
            print(f"✅ Synced {len(donors)} donors to Redis cache and GEO index")
        except Exception as e:
            print(f"⚠️  Warning: Could not sync to Redis/Geo: {e}")
            print("   Continuing without cache/geo sync...")
        
        # Insert requests
        print("🩸 Inserting blood requests...")
        requests = []
        for i, request_data in enumerate(SAMPLE_REQUESTS):
            request_data["hospital_id"] = hospitals[i].id   # <--- ONLY CHANGE
            request = Request(**request_data)
            db.add(request)
            requests.append(request)
        db.commit()
        
        print(f"✅ Created {len(requests)} blood requests")
        
        print("\n" + "="*50)
        print("✅ Database seeding completed successfully!")
        print("="*50)
        print(f"📊 Summary:")
        print(f"   - Hospitals: {len(hospitals)}")
        print(f"   - Donors: {len(donors)}")
        print(f"   - Requests: {len(requests)}")
        print("\n🚀 You can now start the server and test the API at http://localhost:8000/docs")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Starting database seeding...")
    seed_database()