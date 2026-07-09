import redis
import time
import logging
import os

RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 10))
RATE_LIMIT_WINDOW   = int(os.environ.get('RATE_LIMIT_WINDOW', 60))

redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)

# Atomic Lua script — all three operations run server-side in one round trip.
# This prevents the race condition where two replicas each read count=limit-1
# and both admit the request, exceeding the limit by N replicas.
SLIDING_WINDOW_LUA = """
local key       = KEYS[1]
local now       = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit     = tonumber(ARGV[3])
local req_id    = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window_ms)
local count = tonumber(redis.call('ZCARD', key))

if count >= limit then
    return 0
end

redis.call('ZADD', key, now, req_id)
redis.call('EXPIRE', key, math.ceil(window_ms / 1000) + 1)
return 1
"""

_script = None

def _get_script():
    global _script
    if _script is None:
        _script = redis_client.register_script(SLIDING_WINDOW_LUA)
    return _script


def check_rate_limit(client_ip: str) -> bool:
    key        = f'rl:{client_ip}'
    now_ms     = int(time.time() * 1000)
    window_ms  = RATE_LIMIT_WINDOW * 1000
    req_id     = f'{now_ms}:{id(object())}'

    try:
        allowed = _get_script()(
            keys=[key],
            args=[now_ms, window_ms, RATE_LIMIT_REQUESTS, req_id]
        )
        return bool(allowed)
    except redis.RedisError as e:
        # Fail open — Redis outage must not take down the API.
        logging.error('Rate limiter Redis error — failing open: %s', e)
        return True