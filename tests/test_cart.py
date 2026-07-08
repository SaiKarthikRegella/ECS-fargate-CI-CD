def test_add_item_to_cart(client, auth_header, sample_item):
    resp = client.post(
        "/cart/add",
        json={"item_id": sample_item["id"], "quantity": 2},
        headers=auth_header,
    )
    assert resp.status_code == 201
    assert resp.get_json() == {"message": "Item added to cart."}


def test_add_nonexistent_item_returns_404(client, auth_header):
    resp = client.post(
        "/cart/add",
        json={"item_id": 9999, "quantity": 1},
        headers=auth_header,
    )
    assert resp.status_code == 404


def test_get_cart_is_empty_for_new_user(client, auth_header):
    resp = client.get("/cart", headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_get_cart_returns_added_items(client, auth_header, sample_item):
    client.post(
        "/cart/add",
        json={"item_id": sample_item["id"], "quantity": 3},
        headers=auth_header,
    )

    resp = client.get("/cart", headers=auth_header)
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["item_id"] == sample_item["id"]
    assert items[0]["quantity"] == 3


def test_remove_item_from_cart(client, auth_header, sample_item):
    client.post(
        "/cart/add",
        json={"item_id": sample_item["id"], "quantity": 1},
        headers=auth_header,
    )

    resp = client.delete(f"/cart/remove/{sample_item['id']}", headers=auth_header)
    assert resp.status_code == 200

    cart_resp = client.get("/cart", headers=auth_header)
    assert cart_resp.get_json()["items"] == []


def test_remove_item_not_in_cart_returns_404(client, auth_header, sample_item):
    resp = client.delete(f"/cart/remove/{sample_item['id']}", headers=auth_header)
    assert resp.status_code == 404


def test_cart_endpoints_require_auth(client, sample_item):
    # No Authorization header on any of the three cart endpoints
    assert client.get("/cart").status_code == 401
    assert (
        client.post("/cart/add", json={"item_id": sample_item["id"], "quantity": 1}).status_code
        == 401
    )
    assert client.delete(f"/cart/remove/{sample_item['id']}").status_code == 401
