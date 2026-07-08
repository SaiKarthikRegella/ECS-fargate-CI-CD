def test_register_does_not_leak_password(client):
    resp = client.post(
        "/register",
        json={
            "username": "bob",
            "password": "hunter2",
            "email": "bob@example.com",
            "role": "user",
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()

    # The original code returned the plaintext password and the encrypted
    # hash directly in the API response. This test fails loudly if that
    # regresses.
    assert "normal password" not in body
    assert "encrypted_password" not in body
    assert "hunter2" not in str(body)


def test_duplicate_username_is_rejected(client):
    payload = {
        "username": "carol",
        "password": "anotherSecret1",
        "email": "carol@example.com",
        "role": "user",
    }
    first = client.post("/register", json=payload)
    assert first.status_code == 201

    second = client.post("/register", json=payload)
    assert second.status_code == 400
