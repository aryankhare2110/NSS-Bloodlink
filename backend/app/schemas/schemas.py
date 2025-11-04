from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
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

class DonorResponse(DonorBase):
    """Schema for reading a donor"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============ Hospital Schemas ============

class HospitalBase(BaseModel):
    """Base hospital schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Hospital name")
    location: str = Field(..., min_length=1, max_length=200, description="Hospital location")

class HospitalCreate(HospitalBase):
    """Schema for creating a hospital"""
    pass

class HospitalUpdate(BaseModel):
    """Schema for updating a hospital"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, min_length=1, max_length=200)

class HospitalResponse(HospitalBase):
    """Schema for reading a hospital"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

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
    hospital: Optional[HospitalResponse] = None  # Include hospital details if loaded
    
    class Config:
        from_attributes = True

# ============ Request with Hospital Details ============

class RequestWithHospital(RequestResponse):
    """Request schema with hospital information included"""
    hospital: HospitalResponse
    
    class Config:
        from_attributes = True

# ============ Demand Forecast Schemas ============

class DemandForecastResponse(BaseModel):
    """Schema for demand forecast response"""
    id: int
    blood_type: str
    region: str
    forecast_date: datetime
    predicted_demand: float
    confidence: float
    shortage_risk: str
    alert_sent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class DemandHistoryCreate(BaseModel):
    """Schema for creating demand history"""
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    region: str = Field(..., min_length=1, max_length=100)
    demand_units: int = Field(..., ge=0)
    date: datetime
    season: Optional[str] = None
    disease_outbreak: bool = False

# ============ Inventory Schemas ============

class InventoryLevelResponse(BaseModel):
    """Schema for inventory level response"""
    id: int
    hospital_id: int
    blood_type: str
    current_units: int
    min_required: int
    max_capacity: int
    last_updated: datetime
    hospital: Optional[HospitalResponse] = None
    
    class Config:
        from_attributes = True

class InventoryUpdate(BaseModel):
    """Schema for updating inventory"""
    hospital_id: int
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    current_units: int = Field(..., ge=0)

