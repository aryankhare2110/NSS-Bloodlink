# AI module
# This module will contain LangChain and OpenAI logic:
# - Chat functionality
# - Location recommendation
# - Vector database operations
# - Qdrant integration

from app.database import settings

# Initialize OpenAI client when OPENAI_API_KEY is available
openai_client = None
if settings.OPENAI_API_KEY:
    from openai import OpenAI
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# TODO: Initialize LangChain and Qdrant clients

