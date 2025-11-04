from app.database.database import (
    engine,
    SessionLocal,
    Base,
    settings,
)

# Dependency to get database session
def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = ["engine", "SessionLocal", "Base", "settings", "get_db"]
