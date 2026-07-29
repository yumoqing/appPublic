"""
Unified Redis Cache — shared by llmage, pricing, rbac, uapi.
Cross-process safe via Redis + Pub/Sub invalidation.

Usage:
    from appPublic.share_cache import cache_get, cache_invalidate, cache_start_listener

    data = await cache_get("pricing", key, ttl=300, fetcher=lambda: db_query())
    await cache_invalidate("pricing", key)
    await cache_start_listener()
"""
import asyncio
import json
import redis.asyncio as aioredis
from appPublic.log import debug

REDIS_URL = "redis://127.0.0.1:6379"
CHANNEL = "sharecache:invalidate"

_redis = None
_listener_started = False


async def _rc():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def _key(module, k):
    return f"sc:{module}:{k}"


def _cache_enabled(module):
    """Check if cache is enabled for the module in config.json"""
    try:
        from appPublic.jsonConfig import getConfig
        config = getConfig()
        mc = config.module_cache
        if mc is None:
            return True
        return getattr(mc, module, True)
    except Exception:
        return True


async def cache_get(module, key, ttl=300, fetcher=None):
    """Get from cache, or fetch from DB and cache it.
    module: 'pricing', 'rbac', 'uapi', 'llmage'
    key: unique identifier within module
    ttl: seconds (default 300)
    fetcher: async callable that returns the data if cache miss
    """
    if not _cache_enabled(module):
        if fetcher:
            return await fetcher() if asyncio.iscoroutinefunction(fetcher) else await asyncio.coroutine(fetcher)()
        return None

    r = await _rc()
    ck = _key(module, key)
    cached = await r.get(ck)
    if cached is not None:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            return cached

    if fetcher is None:
        return None

    if asyncio.iscoroutinefunction(fetcher):
        data = await fetcher()
    elif callable(fetcher):
        data = fetcher()
    else:
        data = fetcher

    if data is not None:
        await r.setex(ck, ttl, json.dumps(data, default=str))
    return data


async def cache_set(module, key, data, ttl=300):
    """Explicitly set cache value."""
    if not _cache_enabled(module):
        return
    r = await _rc()
    await r.setex(_key(module, key), ttl, json.dumps(data, default=str))


async def cache_invalidate(module, key=None):
    """Invalidate cache. If key is None, invalidate entire module.
    Publishes to all workers via Redis Pub/Sub."""
    r = await _rc()
    if key:
        await r.delete(_key(module, key))
    else:
        keys = await r.keys(_key(module, "*"))
        if keys:
            await r.delete(*keys)
    await r.publish(CHANNEL, json.dumps({"module": module, "key": key or "*"}))
    debug(f"[share_cache] invalidated {module}:{key or '*'}")

# ==== Subscriber (call once per process) ====


async def _subscriber():
    r = await aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    debug("[share_cache] subscriber started, listening...")
    async for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        try:
            data = json.loads(msg["data"])
            mod = data.get("module")
            k = data.get("key")
            rr = await _rc()
            if k == "*":
                keys = await rr.keys(_key(mod, "*"))
                if keys:
                    await rr.delete(*keys)
            else:
                await rr.delete(_key(mod, k))
            debug(f"[share_cache] invalidated from pubsub: {mod}:{k}")
        except Exception as e:
            debug(f"[share_cache] subscriber error: {e}")


def cache_start_listener():
    global _listener_started
    if not _listener_started:
        _listener_started = True
        asyncio.get_event_loop().create_task(_subscriber())
        debug("[share_cache] listener started")
