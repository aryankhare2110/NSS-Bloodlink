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
            model_name="gpt-4o-mini",
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

    # If user explicitly asks to list donors / names
    if re.search(r"\b(list|names|show|display)\b.*\bdonor(s)?\b", text) or any(k in text for k in ["list names", "list donors", "names of donors", "show donors"]):
        return ("list_donor_names", 0.95)

    # If blood group is present and user asks to find donors or mentions "near"
    if parsed.get("blood_group") or any(w in text for w in ["donor", "donors", "find", "near", "nearby"]):
        return ("find_donor", 0.85)

    # Default fallback
    return ("find_donor", 0.5)


def detect_conversation_intent(message: str) -> Optional[str]:
    """Detect simple conversational intents: greeting, thanks, small_talk.

    Returns one of: 'greeting', 'thanks', 'small_talk', or None
    """
    if not message:
        return None
    t = message.lower().strip()
    # Greetings
    if re.match(r'^(hi|hello|hey|good (morning|afternoon|evening))\b', t):
        return 'greeting'
    # Thanks
    if any(w in t for w in ['thank', 'thanks', 'thx', 'thank you']):
        return 'thanks'
    # Small talk / casual questions
    if any(w in t for w in ["how are you", "what's up", "what is your name", "who are you"]):
        return 'small_talk'
    return None


def compose_assistant_reply(text: str, offer: Optional[str] = None, emoji: bool = True) -> str:
    """Compose a final assistant reply that follows behavioral rules:
    - Keep under ~4 lines
    - Be conversational, optionally add emoji, and end with an offer
    """
    if not text:
        text = "I'm here to help."

    # Normalize whitespace and limit to 4 lines
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) > 4:
        lines = lines[:4]
        # indicate truncation politely
        lines[-1] = lines[-1].rstrip('.') + '...'

    reply = "\n".join(lines)

    # Default offer
    if offer is None:
        offer = "Would you like me to check that for you or list nearby donors?"

    if emoji:
        # pick a gentle emoji to match tone
        offer = offer + " ❤️"

    # Ensure reply ends with a single offer line
    if not reply.endswith('?') and not reply.endswith('!'):
        reply = reply.rstrip('.')
    reply = reply + "\n" + offer

    return reply

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
    
    # Build donor list text (limit to 5 for readability)
    donor_names = [f"{donor['name']} ({donor['blood_group']})" for donor in donors[:5]]
    donor_list_text = ", ".join(donor_names)
    count = len(donors)

    # Helper: decide if user explicitly asked for details (names, contact, phone)
    def user_requested_details(msg: str) -> bool:
        low = msg.lower()
        detail_triggers = ["details", "contact", "phone", "call", "message", "name of", "names of", "give me", "list of"]
        # If user explicitly says "show details" or asks for names/contacts, return True
        if any(t in low for t in detail_triggers):
            return True
        # If user asked specifically to "find" or "list" donors, treat as requesting details
        if re.search(r"\b(find|list|show)\b.*\bdonor(s)?\b", low):
            return True
        return False

    wants_details = user_requested_details(message)

    # If LLM is not available, return a concise, conversational summary and offer follow-up
    if llm is None:
        if count == 0:
            return "I couldn't find any available donors matching your criteria. Would you like me to broaden the search?"

        if wants_details:
            if count == 1:
                return f"I found {count} available donor near your location: {donor_list_text}. If you'd like contact details or directions, tell me which donor you'd like to reach out to."
            else:
                return f"I found {count} available donors near your location: {donor_list_text}. Would you like full contact details or directions for any of them?"

        # Default conversational summary without spilling all details
        if count == 1:
            return f"I found 1 available donor nearby. I can share their name and contact details if you want."
        else:
            return f"I found {count} available donors nearby. I can list their names or provide contact/directions for any specific donor — which would you prefer?"
    
    try:
        try:
            from langchain.prompts import ChatPromptTemplate

            # If user didn't request details explicitly, instruct LLM to be conversational
            system_instructions = (
                "You are a friendly assistant for a blood donation platform. Keep responses concise and conversational. "
                "Only include full donor names and contact details if the user explicitly requests them. "
                "Otherwise, give a short summary and offer follow-up options (e.g., 'Would you like names, contact info, or directions?')."
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_instructions),
                ("human", "Original query: {message}\nFound {count} donors: {donor_list}\n\nProvide a friendly, concise response. If the user didn't ask for details, offer follow-ups instead of listing full details.")
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
            # Fallback to simple, conversational formatting
            if wants_details:
                if count == 1:
                    return f"I found {count} available donor near your location: {donor_list_text}. If you'd like contact details or directions, tell me which donor you'd like to reach out to."
                else:
                    return f"I found {count} available donors near your location: {donor_list_text}. Would you like full contact details or directions for any of them?"
            if count == 1:
                return f"I found 1 available donor nearby. I can share their name and contact details if you want."
            else:
                return f"I found {count} available donors nearby. I can list their names or provide contact/directions for any specific donor — which would you prefer?"
            
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
        # First handle simple conversational intents
        conv_intent = detect_conversation_intent(request.message)
        if conv_intent == 'greeting':
            text = "Hi there! 😊 How can I help with blood donors or camps today?"
            return ChatResponse(answer=compose_assistant_reply(text, offer="Want me to find nearby donors?"))
        if conv_intent == 'thanks':
            text = "You're welcome! Happy to help."
            return ChatResponse(answer=compose_assistant_reply(text, offer="Anything else I can do?"))
        if conv_intent == 'small_talk':
            text = "I'm NSS BloodLink's assistant — here to help with donor searches, compatibility, and camps. 😊"
            return ChatResponse(answer=compose_assistant_reply(text))

        # Parse message to extract blood group and region (LLM or regex)
        parsed_info = parse_message_with_llm(request.message)
        blood_group = parsed_info.get("blood_group")
        region = parsed_info.get("region")

        # Detect intent
        intent, confidence = detect_intent(request.message, parsed=parsed_info)

        # Handle compatibility info intent
        if intent == "compatibility_info":
            compatibility = (
                "Here’s a quick compatibility guide:\n"
                "- O-: universal donor\n"
                "- O+: donates to all + types\n"
                "- A/B types: donate to same letter or AB types\n"
                "- AB+: universal recipient"
            )
            if blood_group:
                compatibility += f"\n\nYou asked about {blood_group}. I can search for available {blood_group} donors near {region or 'your area'} if you want."
            return ChatResponse(answer=compose_assistant_reply(compatibility, offer="Want me to search for donors now?"))

        # Recommend location intent
        if intent == "recommend_location":
            top_locations = analyze_donor_density()
            reasons = "; ".join([f"{loc['location']} ({int(loc['score'])})" for loc in top_locations])
            answer = f"Top locations: {reasons}."
            return ChatResponse(answer=compose_assistant_reply(answer, offer="Want details on any location?"))

        # Help intent
        if intent == "help":
            help_text = (
                "I can find donors, explain compatibility, or recommend locations for camps.\n"
                "Try: 'Find O+ donors near AIIMS' or 'Who can donate to B-?'")
            return ChatResponse(answer=compose_assistant_reply(help_text, offer="Want me to try an example?"))

        # If user explicitly requested a list of donor names, return them deterministically
        if intent == "list_donor_names":
            donors = await query_donors(db, blood_group=blood_group, region=region)
            if not donors:
                return ChatResponse(answer=compose_assistant_reply("I couldn't find any donors to list. Would you like me to broaden the search?"))
            names = [d['name'] + f" ({d['blood_group']})" for d in donors[:10]]
            names_text = ", ".join(names)
            answer = f"Here are the donors I found: {names_text}." if len(names) <= 10 else f"I found many donors; here are the first 10: {names_text}."
            return ChatResponse(answer=compose_assistant_reply(answer, offer="Would you like contact details or directions for any of these?"))

        # Default: find donors
        donors = await query_donors(db, blood_group=blood_group, region=region)
        raw_answer = await format_donor_response(request.message, donors)
        return ChatResponse(answer=compose_assistant_reply(raw_answer))

    except Exception:
        # Do not leak internal errors. Give an empathetic message.
        return ChatResponse(answer=compose_assistant_reply("Sorry — I couldn't process that right now. Would you like me to try again later?", offer="Want me to retry?"))

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
