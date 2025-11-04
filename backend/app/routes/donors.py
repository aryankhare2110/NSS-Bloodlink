from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.models import Donor
from app.schemas.schemas import DonorCreate, DonorResponse, DonorUpdate
from app.realtime import broadcast_donor_status_update
from app.services.cache import set_donor_availability
from typing import List

router = APIRouter()

@router.get(
    "/",
    response_model=List[DonorResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all donors",
    description="Retrieve a list of all donors in the system. Optionally filter by availability status.",
    responses={
        200: {
            "description": "List of donors retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Aryan Kumar",
                            "blood_group": "A+",
                            "lat": 28.545,
                            "lng": 77.273,
                            "available": True,
                            "last_donation_date": "2024-01-15T00:00:00",
                            "created_at": "2024-01-01T10:00:00",
                            "updated_at": "2024-01-15T10:00:00"
                        }
                    ]
                }
            }
        }
    }
)
async def get_donors(
    db: Session = Depends(get_db),
    available: bool = None
):
    """
    Get list of all donors.
    
    **Query Parameters:**
    - `available` (optional): Filter by availability status (true/false)
    
    **Returns:**
    - List of donor objects with all details including ID, name, blood group, location, and availability status
    
    **Example:**
    - `GET /donors/` - Get all donors
    - `GET /donors/?available=true` - Get only available donors
    - `GET /donors/?available=false` - Get only unavailable donors
    """
    try:
        query = db.query(Donor)
        
        # Filter by availability if provided
        if available is not None:
            query = query.filter(Donor.available == available)
        
        donors = query.all()
        
        return donors
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post(
    "/",
    response_model=DonorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new donor",
    description="Add a new donor to the database. The donor will be automatically synced to Redis cache.",
    responses={
        201: {
            "description": "Donor created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Aryan Kumar",
                        "blood_group": "A+",
                        "lat": 28.545,
                        "lng": 77.273,
                        "available": True,
                        "last_donation_date": None,
                        "created_at": "2024-01-15T10:00:00",
                        "updated_at": "2024-01-15T10:00:00"
                    }
                }
            }
        }
    }
)
async def create_donor(
    donor_data: DonorCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new donor to the database.
    
    **Request Body:**
    - `name` (required): Donor's full name (max 100 characters)
    - `blood_group` (required): Blood group in format A+, B-, O+, AB+, etc.
    - `lat` (required): Latitude coordinate (-90 to 90)
    - `lng` (required): Longitude coordinate (-180 to 180)
    - `available` (optional): Whether donor is available (default: True)
    - `last_donation_date` (optional): Date of last donation (ISO format)
    
    **Returns:**
    - Created donor object with ID, timestamps, and all details
    
    **Example Request:**
    ```json
    {
        "name": "Aryan Kumar",
        "blood_group": "A+",
        "lat": 28.545,
        "lng": 77.273,
        "available": true,
        "last_donation_date": "2024-01-15T00:00:00"
    }
    ```
    """
    try:
        # Create new donor instance
        new_donor = Donor(**donor_data.model_dump())
        
        # Add to database
        db.add(new_donor)
        db.commit()
        db.refresh(new_donor)
        
        # Sync new donor availability to Redis cache
        await set_donor_availability(new_donor.id, new_donor.available)
        
        return new_donor
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating donor: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.put(
    "/{donor_id}",
    response_model=DonorResponse,
    status_code=status.HTTP_200_OK,
    summary="Update donor information",
    description="Update donor information, primarily availability status. Changes are synced to Redis cache and broadcast via Socket.IO.",
    responses={
        200: {
            "description": "Donor updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Aryan Kumar",
                        "blood_group": "A+",
                        "lat": 28.545,
                        "lng": 77.273,
                        "available": False,
                        "last_donation_date": "2024-01-15T00:00:00",
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-20T10:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Donor not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Donor with ID 999 not found"
                    }
                }
            }
        }
    }
)
async def update_donor_availability(
    donor_id: int,
    donor_update: DonorUpdate,
    db: Session = Depends(get_db)
):
    """
    Update donor information, primarily availability status.
    
    **Path Parameters:**
    - `donor_id` (required): ID of the donor to update
    
    **Request Body (all fields optional):**
    - `available`: New availability status (true/false)
    - `name`: Donor name
    - `blood_group`: Blood group (A+, B-, O+, etc.)
    - `lat`: Latitude coordinate
    - `lng`: Longitude coordinate
    - `last_donation_date`: Last donation date (ISO format)
    
    **Returns:**
    - Updated donor object with all current information
    
    **Example Request:**
    ```json
    {
        "available": false
    }
    ```
    
    **Note:** Updates are automatically synced to Redis cache and broadcast to all connected clients via Socket.IO.
    """
    try:
        # Find donor by ID
        donor = db.query(Donor).filter(Donor.id == donor_id).first()
        
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Donor with ID {donor_id} not found"
            )
        
        # Update only provided fields
        update_data = donor_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(donor, field, value)
        
        # Commit changes
        db.commit()
        db.refresh(donor)
        
        # Sync donor availability to Redis cache
        await set_donor_availability(donor.id, donor.available)
        
        # Broadcast donor status update to all connected clients
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while updating donor: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
