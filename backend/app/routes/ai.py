from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class LocationRecommendationRequest(BaseModel):
    location: str = None

class LocationRecommendationResponse(BaseModel):
    area: str
    reason: str

# TODO: Implement AI routes
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with AI assistant"""
    return ChatResponse(response="AI chat endpoint - TODO: Implement")

@router.post("/recommend-location", response_model=LocationRecommendationResponse)
async def recommend_location(
    request: LocationRecommendationRequest = None,
    db: Session = Depends(get_db)
):
    """Get AI recommendation for camp location"""
    return LocationRecommendationResponse(
        area="South Delhi",
        reason="High Donor Density"
    )

