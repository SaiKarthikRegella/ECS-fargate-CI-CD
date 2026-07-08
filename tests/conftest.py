import os
import sys

import pytest

# Let tests import `app`, `db`, etc. the same way app.py does (no package prefix)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Fresh Flask app + fresh SQLite file per test, so tests never touch
    your real data.db and never leak state between each other."""
    db_path = tmp_path / "test.db"
    flask_app = create_app(db_url=f"sqlite:///{db_path}")
    flask_app.config.update(TESTING=True)
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def register_and_login(
    client,
    username="alice",
    password="Sup3rSecret!",
    email="alice@example.com",
    role="admin",
):
    """Registers a user then logs in, returning the access token.

    Role defaults to "admin" because creating a store/item (needed to test
    the cart) requires admin claims on this API.
    """
    client.post(
        "/register",
        json={
            "username": username,
            "password": password,
            "email": email,
            "role": role,
        },
    )
    resp = client.post(
        "/login",
        json={"username": username, "password": password, "email": email},
    )
    return resp.get_json()["access_token"]


@pytest.fixture
def auth_token(client):
    return register_and_login(client)


@pytest.fixture
def auth_header(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_item(client, auth_header):
    """Creates a store and one item in it, returns the item's JSON."""
    store_resp = client.post(
        "/store", json={"name": "Test Store"}, headers=auth_header
    )
    assert store_resp.status_code == 201, store_resp.get_json()
    store_id = store_resp.get_json()["id"]

    item_resp = client.post(
        "/item",
        json={"name": "Widget", "price": 9.99, "store_id": store_id},
        headers=auth_header,
    )
    assert item_resp.status_code == 201, item_resp.get_json()
    return item_resp.get_json()
