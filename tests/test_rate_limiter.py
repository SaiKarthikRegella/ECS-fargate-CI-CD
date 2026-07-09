from unittest.mock import patch, MagicMock
import redis


def test_check_rate_limit_allows_request(client):
    with patch('resources.rate_limiter._get_client') as mock:
        mock_client = MagicMock()
        mock_client.register_script.return_value = MagicMock(return_value=1)
        mock.return_value = mock_client
        from resources.rate_limiter import check_rate_limit
        result = check_rate_limit('192.168.1.1')
    assert result is True


def test_check_rate_limit_blocks_request(client):
    with patch('resources.rate_limiter._get_client') as mock:
        mock_client = MagicMock()
        mock_client.register_script.return_value = MagicMock(return_value=0)
        mock.return_value = mock_client
        from resources.rate_limiter import check_rate_limit
        result = check_rate_limit('192.168.1.2')
    assert result is False


def test_rate_limiter_fails_open_on_redis_error(client):
    with patch('resources.rate_limiter._get_client') as mock:
        mock.return_value = None  # Redis unavailable
        from resources.rate_limiter import check_rate_limit
        result = check_rate_limit('192.168.1.3')
    assert result is True


def test_health_check_never_rate_limited(client):
    resp = client.get('/health')
    assert resp.status_code == 200


def test_rate_limiter_bypassed_in_testing(client):
    resp = client.get('/cart')
    assert resp.status_code == 401