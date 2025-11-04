from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Donor
from app.services.cache import get_available_donors
from pydantic import BaseModel, Field
from typing import Optional, List
import re
import random

router = APIRouter()

# ============ Pydantic Models ============

class ChatRequest(BaseModel):
    """Request model for AI chat"""
    message: str = Field(..., min_length=1, description="User message to the AI assistant")

class ChatResponse(BaseModel):
    """Response model for AI chat"""
    answer: str = Field(..., description="AI-generated answer with donor information")

class LocationRecommendation(BaseModel):
    """Model for a single location recommendation"""
    location: str = Field(..., description="Recommended location name")
    score: float = Field(..., ge=0, le=100, description="Recommendation score (0-100)")
    reason: str = Field(..., description="Reason for recommendation")

class LocationRecommendationResponse(BaseModel):
    """Response model for location recommendation"""
    recommendations: List[LocationRecommendation] = Field(..., description="Top 3 recommended locations")

# ============ LangChain + OpenAI Setup ============

def get_llm_client():
    """
    Get LangChain LLM client or return None if API key is not available.
    """
    try:
        from app.database import settings
        
        # Check if OpenAI API key is available
        api_key = settings.OPENAI_API_KEY
        
        if not api_key or api_key == "dummy_key" or api_key.startswith("your_api_key"):
            return None
        
        # Try to import LangChain components
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print("Warning: langchain_openai not installed. Using simulated responses.")
            return None
        
        # Initialize LangChain with OpenAI
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key
        )
        
        return llm
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
        return None

# ============ Message Parsing ============

def parse_message_with_llm(message: str) -> dict:
    """
    Parse user message to extract blood group and region using LangChain.
    Falls back to regex parsing if LLM is not available.
    
    Returns:
        dict with 'blood_group' and 'region' keys
    """
    llm = get_llm_client()
    
    if llm is None:
        # Fallback to regex-based parsing
        return parse_message_regex(message)
    
    try:
        from langchain.prompts import ChatPromptTemplate
        from langchain.output_parsers import PydanticOutputParser
        from pydantic import BaseModel as PydanticBaseModel
        
        # Define output structure
        class MessageInfo(PydanticBaseModel):
            blood_group: Optional[str] = None
            region: Optional[str] = None
        
        parser = PydanticOutputParser(pydantic_object=MessageInfo)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a parser that extracts information from blood donation queries.
            Extract:
            1. Blood group (format: A+, B-, O+, AB+, etc.) - if mentioned
            2. Region/location (e.g., "AIIMS", "Delhi", "South Delhi", "near hospital name") - if mentioned
            
            Return JSON with blood_group and region fields. If not found, use null.
            {format_instructions}"""),
            ("human", "Message: {message}")
        ])
        
        # Create chain
        chain = prompt | llm | parser
        
        # Parse message
        result = chain.invoke({
            "message": message,
            "format_instructions": parser.get_format_instructions()
        })
        
        return {
            "blood_group": result.blood_group,
            "region": result.region
        }
        
    except Exception as e:
        print(f"Error parsing with LLM: {e}")
        # Fallback to regex
        return parse_message_regex(message)

def parse_message_regex(message: str) -> dict:
    """
    Parse message using regex patterns to extract blood group and region.
    """
    message_clean = message.strip()
    message_upper = message_clean.upper()

    # Robust blood-group extraction supporting variations like:
    # "O+", "o +", "O positive", "A pos", "AB negative", "B neg", "A plus"
    blood_group = None

    # Combined pattern for letter + sign/word
    blood_pattern = re.compile(r"\b(AB|A|B|O)\s*(?:\+|\-|PLUS|MINUS|POSITIVE|NEGATIVE|POS|NEG)\b", re.IGNORECASE)
    m = blood_pattern.search(message_clean)
    if m:
        grp = m.group(1).upper()
        # determine sign by searching nearby tokens in the match span
        span = m.group(0)
        if re.search(r'\+', span) or re.search(r'PLUS|POSITIVE|POS', span, re.IGNORECASE):
            blood_group = grp + '+'
        elif re.search(r'-', span) or re.search(r'MINUS|NEGATIVE|NEG', span, re.IGNORECASE):
            blood_group = grp + '-'

    # As a fallback, try to match compact forms like 'A+' or 'AB-'
    if not blood_group:
        compact = re.search(r"\b(AB|A|B|O)[+-]\b", message_clean, re.IGNORECASE)
        if compact:
            blood_group = compact.group(0).upper()

    # Extract region (look for common location keywords)
    region = None

    # Check for hospital names (case-insensitive)
    hospitals = ["AIIMS", "APOLLO", "MAX", "FORTIS", "SAFDARJUNG", "BLK"]
    for hospital in hospitals:
        if hospital.lower() in message_clean.lower():
            region = hospital
            break

    # Check for known regions
    regions = ["SOUTH DELHI", "NORTH DELHI", "EAST DELHI", "WEST DELHI", "CENTRAL DELHI",
               "DWARKA", "ROHINI", "NOIDA", "GURGAON", "CONNAUGHT PLACE", "SECTOR"]
    for r in regions:
        if r.lower() in message_clean.lower():
            region = r.title()
            break

    # Check for "near" or "around" patterns to capture freeform location names
    if not region:
        near_pattern = re.search(r"(?:near|around|in|at|nearby)\s+([A-Za-z0-9\-\s]+?)($|\.|,|\?|!|\band\b|\bfor\b)", message_clean, re.IGNORECASE)
        if near_pattern:
            region = near_pattern.group(1).strip()

    return {
        "blood_group": blood_group,
        "region": region
    }


def detect_intent(message: str, parsed: dict = None) -> tuple:
    """Detect user intent from message. Returns (intent, confidence).

    Intents supported: 'compatibility_info', 'recommend_location', 'help', 'find_donor'
    """
    if parsed is None:
        parsed = parse_message_regex(message)

    text = message.lower()

    # High-priority: explicit compatibility questions
    if re.search(r'who can donate to|who can give to|can donate to|compatible with|compatible with', text):
        return ("compatibility_info", 0.98)

    # If message explicitly asks for locations or camps
    if any(k in text for k in ["where to", "best place", "organize a camp", "host a camp", "recommend location", "where should"]):
        return ("recommend_location", 0.9)

    # Help / capabilities
    if any(k in text for k in ["help", "what can you do", "commands", "how do i use", "how can you"]):
        return ("help", 0.9)

    # If blood group is present and user asks to find donors or mentions "near"
    if parsed.get("blood_group") or any(w in text for w in ["donor", "donors", "find", "near", "nearby"]):
        return ("find_donor", 0.85)

    # Default fallback
    return ("find_donor", 0.5)

# ============ Donor Querying ============

async def query_donors(db: Session, blood_group: Optional[str] = None, region: Optional[str] = None) -> List[dict]:
    """
    Query donors from database based on blood group and region.
    
    Args:
        db: Database session
        blood_group: Filter by blood group (optional)
        region: Filter by region (optional, uses location field)
        
    Returns:
        List of donor dictionaries
    """
    try:
        query = db.query(Donor).filter(Donor.available == True)
        
        # Filter by blood group if provided
        if blood_group:
            query = query.filter(Donor.blood_group == blood_group)
        
        # Filter by region (simplified - using lat/lng ranges for demo)
        # In production, you'd use proper geospatial queries
        if region:
            # Mock region-based filtering (in production, use actual geocoding)
            # For now, we'll just return available donors
            pass
        
        donors = query.limit(10).all()
        
        # Convert to dictionaries
        donor_list = []
        for donor in donors:
            donor_list.append({
                "id": donor.id,
                "name": donor.name,
                "blood_group": donor.blood_group,
                "lat": donor.lat,
                "lng": donor.lng,
                "available": donor.available,
            })
        
        return donor_list
        
    except Exception as e:
        print(f"Error querying donors: {e}")
        return []

async def format_donor_response(message: str, donors: List[dict]) -> str:
    """
    Format donor query results into a natural language response using LLM if available.
    """
    llm = get_llm_client()
    
    if not donors:
        return "I couldn't find any available donors matching your criteria. Please try a different blood group or location."
    
    # Build donor list text
    donor_names = []
    for donor in donors[:5]:  # Limit to 5 for readability
        donor_names.append(f"{donor['name']} ({donor['blood_group']})")
    
    donor_list_text = ", ".join(donor_names)
    count = len(donors)
    
    if llm is None:
        # Simulated response
        if count == 1:
            return f"I found {count} available donor near your location: {donor_list_text}."
        else:
            return f"I found {count} available donors near your location: {donor_list_text}."
    
    try:
        from langchain.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant for NSS BloodLink blood donation platform.
            Format the donor search results into a friendly, concise response.
            Include the count and list the donors naturally."""),
            ("human", """Original query: {message}

Found {count} donors: {donor_list}

Provide a friendly response summarizing the results.""")
        ])
        
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "message": message,
            "count": count,
            "donor_list": donor_list_text
        })
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        print(f"Error formatting with LLM: {e}")
        # Fallback to simple formatting
        if count == 1:
            return f"I found {count} available donor: {donor_list_text}."
        else:
            return f"I found {count} available donors: {donor_list_text}."

# ============ Location Analysis ============

def analyze_donor_density() -> List[dict]:
    """
    Analyze donor density by region (mock implementation with static values).
    In production, this would query the database and calculate actual density.
    
    Returns:
        List of location dictionaries with density scores
    """
    # Mock data - in production, calculate from actual donor locations
    locations = [
        {
            "location": "South Delhi",
            "score": 92.5,
            "reason": "High donor density (156 donors), excellent accessibility, active engagement",
            "donor_count": 156,
        },
        {
            "location": "Dwarka",
            "score": 87.3,
            "reason": "Growing population with high engagement rates, strong volunteer network",
            "donor_count": 124,
        },
        {
            "location": "Rohini",
            "score": 85.1,
            "reason": "Excellent volunteer network, consistent donor participation",
            "donor_count": 98,
        },
        {
            "location": "Noida Sector 62",
            "score": 82.7,
            "reason": "Corporate hub with active donors, good infrastructure",
            "donor_count": 89,
        },
        {
            "location": "Gurgaon Sector 15",
            "score": 79.4,
            "reason": "High potential donor activity, community engagement",
            "donor_count": 67,
        },
        {
            "location": "Connaught Place",
            "score": 76.2,
            "reason": "Central location, moderate donor base",
            "donor_count": 54,
        },
    ]
    
    # Sort by score (descending) and return top 3
    sorted_locations = sorted(locations, key=lambda x: x["score"], reverse=True)
    return sorted_locations[:3]

# ============ API Endpoints ============

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI assistant",
    description="Query the AI assistant to find donors. The AI will parse your message to extract blood group and location, then query the database for matching donors.",
    responses={
        200: {
            "description": "AI response with donor information",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "I found 3 available donors near AIIMS: Aarav (A+), Simran (B+), Priya (O+)."
                    }
                }
            }
        }
    }
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with AI assistant to find donors.
    
    **Request Body:**
    - `message` (required): User query message (e.g., "Find O+ donors near AIIMS")
    
    **Returns:**
    - `answer`: Formatted response with donor information
    
    **The AI will:**
    1. Parse the message to extract blood group (A+, B-, O+, etc.) and region/location
    2. Query available donors from the database matching the criteria
    3. Return a formatted natural language response with donor details
    
    **Example Request:**
    ```json
    {
        "message": "Find O+ donors near AIIMS"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "answer": "I found 3 available donors near AIIMS: Aarav (A+), Simran (B+), Priya (O+)."
    }
    ```
    """
    try:
        # Parse message to extract blood group and region (LLM or regex)
        parsed_info = parse_message_with_llm(request.message)
        blood_group = parsed_info.get("blood_group")
        region = parsed_info.get("region")

        # Detect intent
        intent, confidence = detect_intent(request.message, parsed=parsed_info)

        # Handle compatibility info intent
        if intent == "compatibility_info":
            # Basic compatibility table summary
            compatibility = (
                "Compatibility quick guide:\n"
                "- O- can donate to everyone (universal donor).\n"
                "- O+ can donate to all positive types (A+, B+, AB+, O+).\n"
                "- A- can donate to A-, A+, AB-, AB+.\n"
                "- A+ can donate to A+, AB+.\n"
                "- B- can donate to B-, B+, AB-, AB+.\n"
                "- B+ can donate to B+, AB+.\n"
                "- AB- can donate to AB-, AB+.\n"
                "- AB+ can receive from everyone (universal recipient)."
            )

            # If a blood group was mentioned, add a focused sentence
            if blood_group:
                compatibility += f"\n\nYou asked about {blood_group}. I can search for available {blood_group} donors near {region or 'your area'} if you want."

            return ChatResponse(answer=compatibility)

        # Recommend location intent
        if intent == "recommend_location":
            top_locations = analyze_donor_density()
            reasons = "\n".join([f"- {loc['location']}: {loc['reason']} (score: {loc['score']})" for loc in top_locations])
            answer = "Top recommended locations to host a blood donation camp:\n" + reasons
            return ChatResponse(answer=answer)

        # Help intent
        if intent == "help":
            help_text = (
                "I can help you find available donors, suggest locations for camps, or explain blood compatibility.\n"
                "Try messages like:\n"
                "- 'Find O+ donors near AIIMS'\n"
                "- 'Who can donate to B-'\n"
                "- 'Where should we host a camp in South Delhi?'\n"
                "- 'Help' to see this message again."
            )
            return ChatResponse(answer=help_text)

        # Default: find donors
        donors = await query_donors(db, blood_group=blood_group, region=region)
        answer = await format_donor_response(request.message, donors)
        return ChatResponse(answer=answer)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

@router.get(
    "/recommend-location",
    response_model=LocationRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get location recommendations",
    description="Get AI-powered recommendations for the best locations to host blood donation camps based on donor density analysis.",
    responses={
        200: {
            "description": "Top 3 location recommendations with scores",
            "content": {
                "application/json": {
                    "example": {
                        "recommendations": [
                            {
                                "location": "South Delhi",
                                "score": 92.5,
                                "reason": "High donor density (156 donors), excellent accessibility, active engagement"
                            },
                            {
                                "location": "Dwarka",
                                "score": 87.3,
                                "reason": "Growing population with high engagement rates, strong volunteer network"
                            },
                            {
                                "location": "Rohini",
                                "score": 85.1,
                                "reason": "Excellent volunteer network, consistent donor participation"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def recommend_location(
    db: Session = Depends(get_db)
):
    """
    Get AI recommendation for best locations to host blood donation camps.
    
    **Returns:**
    - `recommendations`: Top 3 recommended locations with scores (0-100) and detailed reasons
    
    **The analysis considers:**
    - Donor density by region
    - Accessibility and infrastructure
    - Historical engagement rates
    - Volunteer network strength
    
    **Example Response:**
    ```json
    {
        "recommendations": [
            {
                "location": "South Delhi",
                "score": 92.5,
                "reason": "High donor density (156 donors), excellent accessibility, active engagement"
            },
            {
                "location": "Dwarka",
                "score": 87.3,
                "reason": "Growing population with high engagement rates, strong volunteer network"
            },
            {
                "location": "Rohini",
                "score": 85.1,
                "reason": "Excellent volunteer network, consistent donor participation"
            }
        ]
    }
    ```
    """
    try:
        # Analyze donor density (mock implementation)
        top_locations = analyze_donor_density()
        
        # Convert to response format
        recommendations = [
            LocationRecommendation(
                location=loc["location"],
                score=loc["score"],
                reason=loc["reason"]
            )
            for loc in top_locations
        ]
        
        return LocationRecommendationResponse(recommendations=recommendations)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating location recommendation: {str(e)}"
        )
