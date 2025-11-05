# backend/app/services/geo.py
import time
from typing import List, Tuple
from app.services.cache import get_redis_client  # reuse your existing client
from redis.exceptions import ResponseError

GEO_KEY = "donors:live"
TS_KEY  = "donors:live:ts"  # score = unix ms

def _member(donor_id: int) -> str:
    return f"donor:{donor_id}"

async def upsert_donor_geo(donor_id: int, lat: float, lng: float, accuracy_m: int | None = None) -> None:
    r = await get_redis_client()
    now = int(time.time() * 1000)
    m = _member(donor_id)
    p = r.pipeline()
    p.geoadd(GEO_KEY, (lng, lat, m))  # (lng, lat)
    p.zadd(TS_KEY, {m: now})
    p.hset(f"donor:meta:{donor_id}", mapping={
        "lat": lat, "lng": lng, "accuracy_m": accuracy_m or 0, "updated_at": now
    })
    await p.execute()


async def donors_near(lat: float, lng: float, km: float = 5.0, fresh_ms: int = 10*60*1000):
    r = await get_redis_client()
    rows = await r.geosearch(
        GEO_KEY,
        longitude=lng, latitude=lat,
        radius=km, unit="km",
        withdist=True
    )
    if not rows:
        return []

    # normalize rows → members (str), dists (float)
    members, dists = [], {}
    first = rows[0]
    if isinstance(first, (list, tuple)) and len(first) >= 2:
        for m, dist in rows:
            m = m.decode() if isinstance(m, (bytes, bytearray)) else m
            members.append(m); dists[m] = float(dist)
    else:
        for m in rows:
            m = m.decode() if isinstance(m, (bytes, bytearray)) else m
            members.append(m); dists[m] = 0.0

    # freshness via pipelined ZSCORE (no ZMSCORE at all)
    pipe = r.pipeline()
    for m in members:
        pipe.zscore(TS_KEY, m)
    scores = await pipe.execute()

    cutoff = int(time.time()*1000) - fresh_ms
    out = []
    for m, sc in zip(members, scores):
        if sc is not None and sc >= cutoff:
            donor_id = int(m.split(":", 1)[1])
            out.append((donor_id, dists[m]))
    out.sort(key=lambda x: x[1])
    return out


async def purge_stale(fresh_ms: int = 10 * 60 * 1000) -> int:
    r = await get_redis_client()
    cutoff = int(time.time() * 1000) - fresh_ms
    stale = await r.zrangebyscore(TS_KEY, 0, cutoff)
    if not stale:
        return 0
    p = r.pipeline()
    p.zrem(TS_KEY, *stale)
    p.zrem(GEO_KEY, *stale)
    await p.execute()
    return len(stale)