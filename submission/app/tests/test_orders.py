# tests/test_orders.py
import pytest
from fastapi import status

def test_create_order_for_current_user(client, user_headers, product):
    """
    Test that a logged-in user can create an order for a product.
    """
    resp = client.post(
        "/orders",
        headers=user_headers, # Use the fixture for user headers
        json={
            "product_id": product.id,
            "quantity": 2,
        }
    )
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["product_id"] == product.id
    assert body["quantity"] == 2

def test_create_order_requires_login(client, product):
    """
    Test that creating an order without being logged in returns a 401 Unauthorized.
    """
    resp = client.post(
        "/orders",
        json={
            "product_id": product.id,
            "quantity": 2,
        }
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_order_with_unknown_product_is_400(client, user_headers):
    """
    Test that creating an order with a non-existent product ID returns a 400 Bad Request.
    """
    resp = client.post(
        "/orders",
        headers=user_headers,
        json={
            "product_id": 9999,  # Assuming this product ID does not exist
            "quantity": 1,
        }
    )
    
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.parametrize(
    "payload",
    [
        {"product_id": 1, "quantity": 0},        # quantity must be > 0
        {"product_id": 1, "quantity": -3},       # quantity must be > 0
        {"product_id"},                          # missing quantity
        {"product_id": "abc", "quantity": 1},    # invalid product_id type
    ],
)
def test_invalid_order_payload_is_422(client, user_headers, payload):
    """
    Test that creating an order with invalid payloads returns a 422 Unprocessable Entity.
    """
    resp = client.post(
        "/orders",
        headers=user_headers,
        json=payload,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_missing_order_is_404(client, user_headers):
    """
    Test that trying to retrieve a non-existent order returns a 404 Not Found.
    """
    resp = client.get(
        "/orders/9999",
        header = user_headers
    )
    assert resp.status_code == 422

def test_cannot_view_another_users_order(
    client,
    user_headers,
    other_user_headers,
    product,
):
    """
    Test that a user cannot view another user's order.
    """
    order = client.post(
        "/orders",
        json={
            "product_id": product.id,
            "quantity": 1,
        },
        headers=user_headers
    ).json() # create alice's order    
    
    resp = client.get(f"/orders/{order['id']}", headers=other_user_headers)  # try to access it with bob's account
    
    assert resp.status_code == status.HTTP_403_FORBIDDEN

def test_list_shows_only_own_orders(
    client,
    user_headers,
    other_user_headers,
    product,
):
    """
    Test that the /orders endpoint only returns orders for the logged-in user.
    """
    # create alice's order
    client.post(
        "/orders", 
        json={
            "product_id": product.id,
            "quantity": 1,
        },
        headers=user_headers,
    )
    # create bob's order
    client.post(
            "/orders", 
            json={
                "product_id": product.id,
                "quantity": 1,
            },
            headers=other_user_headers,
    ) 

    orders = client.get("/orders", headers=user_headers).json()
    assert len(orders) == 1 
    assert orders[0]["quantity"] == 1

def test_patch_updates_only_sent_fields(client, user_headers, product):
    """
    Test that PATCH /orders/{id} updates only the fields provided in the request.
    """
    order = client.post(
        "/orders", 
        json={
            "product_id": product.id,
            "quantity": 2,
        },
        headers=user_headers,
    )
    resp = client.patch(
        f"/orders/{order['id']}",
        json={"status": "shipped"},  # only updating the status
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "shipped"
    assert resp.json()["quantity"] == 2     # untouched by the PATCH

def test_customer_cannot_delete_order(client, user_headers, product):
    order = client.post(
        "/order", 
        json={
            "product_id": product.id,
            "quantity": 1,
        },
        headers=user_headers,
    ).json()

    assert client.delete(
        f"/orders/{order['id']}",
        headers=user_headers,
    ).status_code == status.HTTP_403_FORBIDDEN

def test_admin_can_delete_order(client, user_headers, admin_headers, product):
    """
    Test that an admin user can delete an order.
    """
    order = client.post(
        "/orders",
        json={
            "product_id": product.id,
            "quantity": 1,
        },
        headers=user_headers,
    ).json()

    assert client.delete(
        f"/orders/{order['id']}",
        headers=admin_headers
    ).status_code == status.HTTP_204_NO_CONTENT    

    assert client.get(
        f"/orders/{order['id']}",
        headers=admin_headers
    ).status_code == status.HTTP_404_NOT_FOUND

