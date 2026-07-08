def test_health_check_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_health_check_does_not_require_auth(client):
    # No Authorization header at all — ALB health checks can't carry a JWT.
    resp = client.get("/health")
    assert resp.status_code == 200
