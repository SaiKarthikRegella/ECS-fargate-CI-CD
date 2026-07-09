import redis
import time
import logging
import os

RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 10))
RATE_LIMIT_WINDOW   = int(os.environ.get('RATE_LIMIT_WINDOW', 60))

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

def _get_client():
    try:
        client = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        # Test the connection immediately
        client.ping()
        return client
    except Exception as e:
        logging.error('Redis unavailable: %s', e)
        return None


def check_rate_limit(client_ip: str) -> bool:
    client = _get_client()
    if client is None:
        # Fail open — Redis unavailable
        return True

    key       = f'rl:{client_ip}'
    now_ms    = int(time.time() * 1000)
    window_ms = RATE_LIMIT_WINDOW * 1000
    req_id    = f'{now_ms}:{id(object())}'

    try:
        script = client.register_script(SLIDING_WINDOW_LUA)
        allowed = script(
            keys=[key],
            args=[now_ms, window_ms, RATE_LIMIT_REQUESTS, req_id]
        )
        return bool(allowed)
    except Exception as e:
        logging.error('Rate limiter error — failing open: %s', e)
        return True