from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database.database import Base

class UrgencyLevel(str, enum.Enum):
    """Urgency levels for blood requests"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class RequestStatus(str, enum.Enum):
    """Status of blood requests"""
    PENDING = "Pending"
    ACTIVE = "Active"
    FULFILLED = "Fulfilled"
    CANCELLED = "Cancelled"

class Donor(Base):
    """Donor model"""
    __tablename__ = "donors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    blood_group = Column(String(5), nullable=False, index=True)  # A+, B-, O+, etc.
    lat = Column(Float, nullable=False)  # Latitude
    lng = Column(Float, nullable=False)  # Longitude
    available = Column(Boolean, default=True, nullable=False, index=True)
    last_donation_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    requests = relationship("Request", back_populates="donor")

class Hospital(Base):
    """Hospital model"""
    __tablename__ = "hospitals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    location = Column(String(200), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    requests = relationship("Request", back_populates="hospital")

class Request(Base):
    """Blood request model"""
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    blood_type = Column(String(5), nullable=False, index=True)  # A+, B-, O+, etc.
    urgency = Column(SQLEnum(UrgencyLevel), nullable=False, default=UrgencyLevel.MEDIUM, index=True)
    status = Column(SQLEnum(RequestStatus), nullable=False, default=RequestStatus.PENDING, index=True)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=True)  # Assigned donor (if any)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    hospital = relationship("Hospital", back_populates="requests")
    donor = relationship("Donor", back_populates="requests", foreign_keys=[donor_id])

