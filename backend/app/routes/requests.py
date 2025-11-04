from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.models import Request, Hospital, RequestStatus
from app.schemas.schemas import RequestCreate, RequestResponse, RequestWithHospital
from app.realtime import broadcast_new_request
from typing import List
from pydantic import BaseModel

router = APIRouter()

class RequestStatusUpdate(BaseModel):
    """Schema for updating request status"""
    status: RequestStatus

@router.get(
    "/",
    response_model=List[RequestWithHospital],
    status_code=status.HTTP_200_OK,
    summary="Get all blood requests",
    description="Retrieve all blood requests with hospital details. Optionally filter by status or hospital ID.",
    responses={
        200: {
            "description": "List of requests retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "hospital_id": 1,
                            "blood_type": "O+",
                            "urgency": "Critical",
                            "status": "Pending",
                            "donor_id": None,
                            "created_at": "2024-01-20T10:00:00",
                            "updated_at": "2024-01-20T10:00:00",
                            "hospital": {
                                "id": 1,
                                "name": "Apollo Hospital",
                                "location": "Delhi",
                                "created_at": "2024-01-01T10:00:00",
                                "updated_at": "2024-01-01T10:00:00"
                            }
                        }
                    ]
                }
            }
        }
    }
)
async def get_requests(
    db: Session = Depends(get_db),
    status_filter: RequestStatus = None,
    hospital_id: int = None
):
    """
    Get all blood requests.
    
    **Query Parameters:**
    - `status_filter` (optional): Filter by request status (Pending, Active, Fulfilled, Cancelled)
    - `hospital_id` (optional): Filter by hospital ID
    
    **Returns:**
    - List of request objects with hospital details included
    
    **Example:**
    - `GET /requests/` - Get all requests
    - `GET /requests/?status_filter=Pending` - Get only pending requests
    - `GET /requests/?hospital_id=1` - Get requests for hospital ID 1
    """
    try:
        query = db.query(Request)
        
        # Filter by status if provided
        if status_filter is not None:
            query = query.filter(Request.status == status_filter)
        
        # Filter by hospital_id if provided
        if hospital_id is not None:
            query = query.filter(Request.hospital_id == hospital_id)
        
        # Join with hospital for eager loading
        requests = query.options(
            joinedload(Request.hospital)
        ).all()
        
        return requests
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
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new blood request",
    description="Create a new blood donation request for a hospital. The request will be broadcast to all connected clients via Socket.IO.",
    responses={
        201: {
            "description": "Request created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "hospital_id": 1,
                        "blood_type": "O+",
                        "urgency": "Critical",
                        "status": "Pending",
                        "donor_id": None,
                        "created_at": "2024-01-20T10:00:00",
                        "updated_at": "2024-01-20T10:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Hospital not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Hospital with ID 999 not found"
                    }
                }
            }
        }
    }
)
async def create_request(
    request_data: RequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new blood request.
    
    **Request Body:**
    - `hospital_id` (required): ID of the requesting hospital
    - `blood_type` (required): Required blood type in format A+, B-, O+, AB+, etc.
    - `urgency` (optional): Urgency level - Low, Medium, High, Critical (default: Medium)
    - `status` (optional): Request status - Pending, Active, Fulfilled, Cancelled (default: Pending)
    
    **Returns:**
    - Created request object with ID, timestamps, and all details
    
    **Example Request:**
    ```json
    {
        "hospital_id": 1,
        "blood_type": "O+",
        "urgency": "Critical",
        "status": "Pending"
    }
    ```
    
    **Note:** New requests are automatically broadcast to all connected clients via Socket.IO.
    """
    try:
        # Verify hospital exists
        hospital = db.query(Hospital).filter(Hospital.id == request_data.hospital_id).first()
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hospital with ID {request_data.hospital_id} not found"
            )
        
        # Create new request instance
        new_request = Request(**request_data.model_dump())
        
        # Add to database
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        # Load hospital name for broadcast
        hospital = db.query(Hospital).filter(Hospital.id == new_request.hospital_id).first()
        
        # Broadcast new request to all connected clients
        await broadcast_new_request({
            "id": new_request.id,
            "hospital_id": new_request.hospital_id,
            "hospital_name": hospital.name if hospital else None,
            "blood_type": new_request.blood_type,
            "urgency": new_request.urgency.value,
            "status": new_request.status.value,
            "created_at": new_request.created_at.isoformat() if new_request.created_at else None,
        })
        
        return new_request
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating request: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.put(
    "/{request_id}/status",
    response_model=RequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Update request status",
    description="Update the status of a blood request (e.g., mark as Fulfilled when donor is assigned).",
    responses={
        200: {
            "description": "Request status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "hospital_id": 1,
                        "blood_type": "O+",
                        "urgency": "Critical",
                        "status": "Fulfilled",
                        "donor_id": 5,
                        "created_at": "2024-01-20T10:00:00",
                        "updated_at": "2024-01-20T11:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Request not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Request with ID 999 not found"
                    }
                }
            }
        }
    }
)
async def update_request_status(
    request_id: int,
    status_update: RequestStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update request status.
    
    **Path Parameters:**
    - `request_id` (required): ID of the request to update
    
    **Request Body:**
    - `status` (required): New status - Pending, Active, Fulfilled, Cancelled
    
    **Returns:**
    - Updated request object with new status
    
    **Example Request:**
    ```json
    {
        "status": "Fulfilled"
    }
    ```
    """
    try:
        # Find request by ID
        request = db.query(Request).filter(Request.id == request_id).first()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request with ID {request_id} not found"
            )
        
        # Update status
        request.status = status_update.status
        
        # Commit changes
        db.commit()
        db.refresh(request)
        
        return request
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while updating request status: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
