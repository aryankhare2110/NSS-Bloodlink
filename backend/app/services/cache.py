import redis.asyncio as redis
from app.database import settings
from typing import List, Optional
import json

# Global Redis client
redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client connection.
    
    Returns:
        Redis client instance
        
    Raises:
        ConnectionError: If Redis connection fails
    """
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await redis_client.ping()
            print("✅ Redis connection established")
            
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            raise ConnectionError(f"Could not connect to Redis: {e}")
    
    return redis_client

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        print("✅ Redis connection closed")

# ============ Donor Availability Cache ============

async def set_donor_availability(donor_id: int, available: bool) -> bool:
    """
    Store donor availability in Redis cache.
    
    Args:
        donor_id: ID of the donor
        available: Availability status (True/False)
        
    Returns:
        True if successful, False otherwise
        
    Key format: donor:{id}
    Value: "available" or "unavailable"
    """
    try:
        client = await get_redis_client()
        key = f"donor:{donor_id}"
        value = "available" if available else "unavailable"
        
        # Set with no expiration (or set expiration as needed)
        await client.set(key, value)
        
        return True
    except Exception as e:
        print(f"❌ Error setting donor availability in cache: {e}")
        return False

async def get_donor_availability(donor_id: int) -> Optional[bool]:
    """
    Get donor availability from Redis cache.
    
    Args:
        donor_id: ID of the donor
        
    Returns:
        True if available, False if unavailable, None if not in cache
    """
    try:
        client = await get_redis_client()
        key = f"donor:{donor_id}"
        value = await client.get(key)
        
        if value is None:
            return None
        
        return value == "available"
    except Exception as e:
        print(f"❌ Error getting donor availability from cache: {e}")
        return None

async def delete_donor_availability(donor_id: int) -> bool:
    """
    Delete donor availability from Redis cache.
    
    Args:
        donor_id: ID of the donor
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis_client()
        key = f"donor:{donor_id}"
        await client.delete(key)
        return True
    except Exception as e:
        print(f"❌ Error deleting donor availability from cache: {e}")
        return False

async def get_available_donors() -> List[int]:
    """
    Get list of donor IDs marked as available in Redis cache.
    
    Returns:
        List of donor IDs that are available
    """
    try:
        client = await get_redis_client()
        
        # Get all keys matching pattern "donor:*"
        keys = await client.keys("donor:*")
        
        available_donor_ids = []
        
        # Check each key's value
        for key in keys:
            value = await client.get(key)
            if value == "available":
                # Extract donor ID from key (donor:123 -> 123)
                donor_id = int(key.split(":")[1])
                available_donor_ids.append(donor_id)
        
        return available_donor_ids
        
    except Exception as e:
        print(f"❌ Error getting available donors from cache: {e}")
        return []

async def sync_all_donors_to_cache(donors_data: List[dict]) -> bool:
    """
    Sync all donors to Redis cache in batch.
    
    Args:
        donors_data: List of donor dictionaries with 'id' and 'available' keys
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis_client()
        
        # Use pipeline for batch operations
        async with client.pipeline() as pipe:
            for donor in donors_data:
                key = f"donor:{donor['id']}"
                value = "available" if donor.get('available', False) else "unavailable"
                await pipe.set(key, value)
            
            await pipe.execute()
        
        return True
    except Exception as e:
        print(f"❌ Error syncing donors to cache: {e}")
        return False

async def clear_all_donor_cache() -> bool:
    """
    Clear all donor availability entries from Redis cache.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis_client()
        keys = await client.keys("donor:*")
        
        if keys:
            await client.delete(*keys)
        
        return True
    except Exception as e:
        print(f"❌ Error clearing donor cache: {e}")
        return False

