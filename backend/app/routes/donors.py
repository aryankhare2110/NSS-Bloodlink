# backend/app/routes/donors.py
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.models import Donor
from app.schemas.schemas import DonorCreate, DonorResponse, DonorUpdate
from app.realtime import broadcast_donor_status_update
from app.services.cache import set_donor_availability
from app.services.geo import upsert_donor_geo, donors_near
from app.services.notify import send_email

router = APIRouter()

# ---------- Response models ----------
class DonorNearResponse(BaseModel):
    id: int
    name: str
    blood_group: str
    email: Optional[str] = None
    phone: Optional[str] = None
    lat: float
    lng: float
    available: bool
    last_donation_date: Optional[str] = None
    distance_km: float

class NotifyByLocation(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    km: float = Field(default=5.0, gt=0)
    fresh_min: int = Field(default=10, gt=0)             # recent location updates window
    blood_group: Optional[str] = None                    # e.g. "O+"
    available: Optional[bool] = True                     # default: only available
    contactable_only: bool = True                        # require email/phone
    limit: int = Field(default=100, gt=0, le=1000)       # safety cap
    channels: List[str] = Field(default_factory=lambda: ["email"])  # future: "sms", "whatsapp"

class NotifyResult(BaseModel):
    requested: int
    matched: int
    notified: int
    channel_counts: Dict[str, int]
    recipients: List[DonorNearResponse]

# ---------- List all donors ----------
@router.get(
    "/",
    response_model=List[DonorResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all donors",
    description="Retrieve a list of all donors. Optionally filter by availability."
)
async def get_donors(
    db: Session = Depends(get_db),
    available: Optional[bool] = None
):
    try:
        q = db.query(Donor)
        if available is not None:
            q = q.filter(Donor.available == available)
        return q.all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# ---------- Create donor ----------
@router.post(
    "/",
    response_model=DonorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new donor",
    description="Add a new donor and sync to Redis (availability + GEO)."
)
async def create_donor(
    donor_data: DonorCreate,
    db: Session = Depends(get_db)
):
    try:
        new_donor = Donor(**donor_data.model_dump())
        db.add(new_donor)
        db.commit()
        db.refresh(new_donor)

        if new_donor.lat is not None and new_donor.lng is not None:
            await upsert_donor_geo(new_donor.id, new_donor.lat, new_donor.lng)
        await set_donor_availability(new_donor.id, new_donor.available)

        return new_donor
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error while creating donor: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# ---------- Nearby donors (for UI listing) ----------
@router.get(
    "/nearby",
    response_model=List[DonorNearResponse],
    summary="Find nearby donors (Redis GEO) with contact info"
)
async def donors_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    km: float = Query(5.0, gt=0),
    fresh_min: int = Query(10, gt=0),
    blood_group: Optional[str] = None,
    available: Optional[bool] = True,
    contactable_only: bool = True,
    db: Session = Depends(get_db),
):
    try:
        pairs = await donors_near(lat, lng, km=km, fresh_ms=fresh_min * 60 * 1000)  # [(id, km)]
        if not pairs:
            return []
        id_to_km: Dict[int, float] = dict(pairs)
        ids = list(id_to_km.keys())

        q = db.query(Donor).filter(Donor.id.in_(ids))
        if blood_group is not None:
            q = q.filter(Donor.blood_group == blood_group)
        if available is not None:
            q = q.filter(Donor.available == available)
        if contactable_only:
            q = q.filter(or_(Donor.email.isnot(None), Donor.phone.isnot(None)))

        donors = q.all()
        donors.sort(key=lambda d: id_to_km.get(d.id, float("inf")))

        out: List[DonorNearResponse] = []
        for d in donors:
            out.append(DonorNearResponse(
                id=d.id,
                name=d.name,
                blood_group=d.blood_group,
                email=d.email,
                phone=d.phone,
                lat=d.lat,
                lng=d.lng,
                available=d.available,
                last_donation_date=d.last_donation_date.isoformat() if d.last_donation_date else None,
                distance_km=round(id_to_km[d.id], 3),
            ))
        return out
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# ---------- Update donor ----------
@router.put(
    "/{donor_id}",
    response_model=DonorResponse,
    status_code=status.HTTP_200_OK,
    summary="Update donor information",
    description="Update donor info (availability, coords, etc.). Syncs to Redis and broadcasts via Socket.IO."
)
async def update_donor(
    donor_id: int,
    donor_update: DonorUpdate,
    db: Session = Depends(get_db)
):
    try:
        donor = db.query(Donor).filter(Donor.id == donor_id).first()
        if not donor:
            raise HTTPException(status_code=404, detail=f"Donor with ID {donor_id} not found")

        for field, value in donor_update.model_dump(exclude_unset=True).items():
            setattr(donor, field, value)

        db.commit()
        db.refresh(donor)

        if donor.lat is not None and donor.lng is not None:
            await upsert_donor_geo(donor.id, donor.lat, donor.lng)
        await set_donor_availability(donor.id, donor.available)

        await broadcast_donor_status_update({
            "id": donor.id,
            "name": donor.name,
            "blood_group": donor.blood_group,
            "available": donor.available,
            "last_donation_date": donor.last_donation_date.isoformat() if donor.last_donation_date else None,
            "lat": donor.lat,
            "lng": donor.lng,
        })
        return donor
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error while updating donor: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# ---------- NEW: Notify donors by location (server-side search + send) ----------
@router.post(
    "/notify/by-location",
    response_model=NotifyResult,
    summary="Find nearby donors by location and notify them."
)
async def notify_by_location(payload: NotifyByLocation, db: Session = Depends(get_db)):
    # 1) candidate ids by distance+freshness from Redis
    pairs = await donors_near(
        payload.lat, payload.lng,
        km=payload.km,
        fresh_ms=payload.fresh_min * 60 * 1000
    )
    if not pairs:
        return NotifyResult(requested=0, matched=0, notified=0, channel_counts={}, recipients=[])

    id_to_km: Dict[int, float] = dict(pairs)
    ids = list(id_to_km.keys())[: payload.limit]

    # 2) load donors from DB + filters
    q = db.query(Donor).filter(Donor.id.in_(ids))
    if payload.blood_group is not None:
        q = q.filter(Donor.blood_group == payload.blood_group)
    if payload.available is not None:
        q = q.filter(Donor.available == payload.available)
    if payload.contactable_only:
        q = q.filter(or_(Donor.email.isnot(None), Donor.phone.isnot(None)))

    donors = q.all()
    if not donors:
        return NotifyResult(requested=len(ids), matched=0, notified=0, channel_counts={}, recipients=[])

    # 3) order by distance + serialize
    donors.sort(key=lambda d: id_to_km.get(d.id, float("inf")))
    recipients: List[DonorNearResponse] = []
    for d in donors:
        recipients.append(DonorNearResponse(
            id=d.id,
            name=d.name,
            blood_group=d.blood_group,
            email=d.email,
            phone=d.phone,
            lat=d.lat,
            lng=d.lng,
            available=d.available,
            last_donation_date=d.last_donation_date.isoformat() if d.last_donation_date else None,
            distance_km=round(id_to_km[d.id], 3),
        ))

    # 4) notify (email channel implemented)
    notified = 0
    channel_counts: Dict[str, int] = {ch: 0 for ch in payload.channels}
    for r in recipients:
        if "email" in payload.channels and r.email:
            subject = f"🚨 Urgent need for {r.blood_group} blood nearby"
            message = (
                f"Dear {r.name},\n\n"
                f"A nearby hospital urgently needs {r.blood_group} blood.\n"
                f"Approx. location: {payload.lat:.3f}, {payload.lng:.3f} (≤ {payload.km} km)\n\n"
                f"Thank you ❤️\n- NSS BloodLink"
            )
            send_email(r.email, subject, message)
            notified += 1
            channel_counts["email"] += 1

        # placeholders for future:
        # if "sms" in payload.channels and r.phone: send_sms(...)
        # if "whatsapp" in payload.channels and r.phone: send_whatsapp(...)

    # optional: don’t echo back huge lists
    return NotifyResult(
        requested=len(ids),
        matched=len(recipients),
        notified=notified,
        channel_counts=channel_counts,
        recipients=recipients[:50],
    )