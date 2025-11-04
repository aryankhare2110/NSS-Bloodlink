from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, settings
from app.services.db_utils import init_db
from app.services.cache import get_redis_client, close_redis
from app.realtime import socketio_app

# Create FastAPI app with enhanced OpenAPI docs
app = FastAPI(
    title="NSS BloodLink API",
    description="AI-powered Blood Donation Platform API for managing donors, requests, and blood donation camps.",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
    openapi_url="/openapi.json",  # OpenAPI JSON schema
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event: Connect to database and Redis
@app.on_event("startup")
async def startup_event():
    """Initialize database connection and Redis cache on startup"""
    # Initialize database tables
    init_db()
    print("✅ Database connection established")
    
    # Initialize Redis connection
    try:
        await get_redis_client()
    except Exception as e:
        print(f"⚠️  Redis connection failed (continuing without cache): {e}")

# Shutdown event: Close database and Redis connections
@app.on_event("shutdown")
async def shutdown_event():
    """Close database and Redis connections on shutdown"""
    engine.dispose()
    print("✅ Database connection closed")
    
    # Close Redis connection
    await close_redis()

# Root route
@app.get("/")
async def root():
    return {"message": "NSS BloodLink API running"}

# Health check route
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include routers
from app.routes import donors, requests
from app.ai.ai_routes import router as ai_router

app.include_router(donors.router, prefix="/donors", tags=["Donors"])
app.include_router(requests.router, prefix="/requests", tags=["Requests"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])

# Mount Socket.IO ASGI app at /ws
app.mount("/ws", socketio_app)
