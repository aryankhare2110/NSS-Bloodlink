from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine, Base
from typing import Generator

def get_session() -> Generator[Session, None, None]:
    """
    Helper function to get a database session.
    Use this in services or when you need a session outside of FastAPI dependencies.
    
    Usage:
        with get_session() as db:
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize the database by creating all tables.
    This should be called once during application startup or migration.
    
    Usage:
        init_db()
    """
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def drop_db() -> None:
    """
    Drop all database tables.
    WARNING: This will delete all data. Use with caution!
    
    Usage:
        drop_db()
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")

def reset_db() -> None:
    """
    Reset the database by dropping and recreating all tables.
    WARNING: This will delete all data. Use with caution!
    
    Usage:
        reset_db()
    """
    drop_db()
    init_db()
    print("✅ Database reset complete")

__all__ = ["get_session", "init_db", "drop_db", "reset_db"]

