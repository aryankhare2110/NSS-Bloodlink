from app.database import engine, Base
from app.models import models

print("🔨 Dropping ALL tables...")
Base.metadata.drop_all(bind=engine)

print("📦 Creating tables...")
Base.metadata.create_all(bind=engine)

print("✅ Database reset complete!")
