from socketio import AsyncServer, ASGIApp
from fastapi import FastAPI
from app.database import settings
import json

# Create Socket.IO server
sio = AsyncServer(
    cors_allowed_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    async_mode="asgi",
    logger=True,
    engineio_logger=True,
)

# Create ASGI app wrapper
socketio_app = ASGIApp(sio)

# ============ Socket.IO Event Handlers ============

@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"✅ Client connected: {sid}")
    await sio.emit("connected", {"message": "Connected to NSS BloodLink"}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"❌ Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    """Allow clients to join specific rooms (e.g., 'donors', 'requests')"""
    room = data.get("room", "general")
    sio.enter_room(sid, room)
    await sio.emit("joined_room", {"room": room}, room=sid)
    print(f"Client {sid} joined room: {room}")

@sio.event
async def leave_room(sid, data):
    """Allow clients to leave specific rooms"""
    room = data.get("room", "general")
    sio.leave_room(sid, room)
    await sio.emit("left_room", {"room": room}, room=sid)
    print(f"Client {sid} left room: {room}")

# ============ Broadcast Functions ============

async def broadcast_donor_status_update(donor_data: dict):
    """
    Broadcast donor status update to all connected clients.
    
    Args:
        donor_data: Dictionary containing donor information
            {
                "id": int,
                "name": str,
                "blood_group": str,
                "available": bool,
                "last_donation_date": str (optional)
            }
    """
    try:
        event_data = {
            "type": "donor_status_update",
            "data": donor_data,
            "timestamp": None  # Will be set by client or can use datetime.now().isoformat()
        }
        
        # Broadcast to all clients
        await sio.emit("donor_status_update", event_data)
        
        # Also broadcast to 'donors' room if clients are subscribed
        await sio.emit("donor_status_update", event_data, room="donors")
        
        print(f"📢 Broadcasted donor status update: Donor {donor_data.get('id')} - Available: {donor_data.get('available')}")
        
    except Exception as e:
        print(f"❌ Error broadcasting donor status update: {e}")

async def broadcast_new_request(request_data: dict):
    """
    Broadcast new blood request to all connected clients.
    
    Args:
        request_data: Dictionary containing request information
            {
                "id": int,
                "hospital_id": int,
                "hospital_name": str (optional),
                "blood_type": str,
                "urgency": str,
                "status": str,
                "created_at": str
            }
    """
    try:
        event_data = {
            "type": "new_request",
            "data": request_data,
            "timestamp": None  # Will be set by client or can use datetime.now().isoformat()
        }
        
        # Broadcast to all clients
        await sio.emit("new_request", event_data)
        
        # Also broadcast to 'requests' room if clients are subscribed
        await sio.emit("new_request", event_data, room="requests")
        
        print(f"📢 Broadcasted new request: Request {request_data.get('id')} - {request_data.get('blood_type')} - {request_data.get('urgency')}")
        
    except Exception as e:
        print(f"❌ Error broadcasting new request: {e}")

# ============ Helper Functions ============

async def get_connected_clients():
    """Get list of connected client IDs"""
    return list(sio.manager.rooms.get("/", {}).keys())

async def get_room_clients(room: str):
    """Get list of clients in a specific room"""
    return list(sio.manager.rooms.get("/", {}).get(room, set()))

