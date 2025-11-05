# backend/app/schemas/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.models.models import UrgencyLevel, RequestStatus


# ============ Donor Schemas ============

class DonorBase(BaseModel):
    """Base donor schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Donor full name")
    blood_group: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$", description="Blood group (e.g., A+, O-)")
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    lng: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    available: bool = Field(default=True, description="Whether donor is currently available")
    last_donation_date: Optional[datetime] = Field(None, description="Date of last donation")
    # contact fields
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class DonorCreate(DonorBase):
    """Schema for creating a donor"""
    pass

class DonorUpdate(BaseModel):
    """Schema for updating a donor"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    blood_group: Optional[str] = Field(None, pattern=r"^(A|B|AB|O)[+-]$")
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    available: Optional[bool] = None
    last_donation_date: Optional[datetime] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class DonorResponse(DonorBase):
    """Schema for reading a donor"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Hospital Schemas ============

class HospitalBase(BaseModel):
    """Base hospital schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Hospital name")
    location: str = Field(..., min_length=1, max_length=200, description="Hospital location")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    lng: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")

class HospitalCreate(HospitalBase):
    """Schema for creating a hospital"""
    pass

class HospitalUpdate(BaseModel):
    """Schema for updating a hospital"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)

class HospitalResponse(HospitalBase):
    """Schema for reading a hospital"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Request Schemas ============

class RequestBase(BaseModel):
    """Base request schema"""
    hospital_id: int = Field(..., description="ID of the requesting hospital")
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$", description="Required blood type")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM, description="Urgency level")
    status: RequestStatus = Field(default=RequestStatus.PENDING, description="Request status")

class RequestCreate(RequestBase):
    """Schema for creating a request"""
    pass

class RequestUpdate(BaseModel):
    """Schema for updating a request"""
    hospital_id: Optional[int] = None
    blood_type: Optional[str] = Field(None, pattern=r"^(A|B|AB|O)[+-]$")
    urgency: Optional[UrgencyLevel] = None
    status: Optional[RequestStatus] = None
    donor_id: Optional[int] = Field(None, description="ID of assigned donor")

class RequestResponse(RequestBase):
    """Schema for reading a request"""
    id: int
    donor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    hospital: Optional["HospitalResponse"] = None  # include hospital details if loaded

    model_config = ConfigDict(from_attributes=True)


# ============ Request with Hospital Details ============

class RequestWithHospital(RequestResponse):
    """Request schema with hospital information included"""
    hospital: HospitalResponse

    model_config = ConfigDict(from_attributes=True)