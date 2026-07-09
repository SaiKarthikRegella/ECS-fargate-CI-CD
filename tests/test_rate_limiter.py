from unittest.mock import patch, MagicMock
import redis


def test_check_rate_limit_allows_request(client):
    with patch('resources.rate_limiter._get_script') as mock:
        mock.return_value = MagicMock(return_value=1)
        from resources.rate_limiter import check_rate_limit
        result = check_rate_limit('192.168.1.1')
    assert result is True


def test_check_rate_limit_blocks_request(client):
    with patch('resources.rate_limiter._get_script') as mock:
        mock.return_value = MagicMock(return_value=0)
        from resources.rate_limiter import check_rate_limit
        result = check_rate_limit('192.168.1.2')
    assert result is False


def test_rate_limiter_fails_open_on_redis_error(client):
    with patch('resources.rate_limiter._get_script') as mock:
        mock.return_value = MagicMock(
            side_effect=redis.RedisError('connection refused')
        )
        from resources.rate_limiter import check_rate_limit
        result = check_rate_limit('192.168.1.3')
    assert result is True


def test_health_check_never_rate_limited(client):
    resp = client.get('/health')
    assert resp.status_code == 200


def test_rate_limiter_bypassed_in_testing(client):
    # TESTING=True is set in conftest — all endpoints should work normally
    resp = client.get('/cart')
    assert resp.status_code == 401  # 401 not 429 — auth check, not rate limit