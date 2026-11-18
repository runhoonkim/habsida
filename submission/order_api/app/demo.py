import httpx

with httpx.Client(base_url="http://127.0.0.1:8000") as c:
    c.post("/register", json={"email": "ada@example.com", "password": "secret",
                              "full_name": "Ada Lovelace"})
    token = c.post("/token", data={"username": "ada@example.com",
                                   "password": "secret"}).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    order = c.post("/orders", json={"product_id": 3, "quantity": 2}, headers=auth).json()
    print(c.get("/orders", headers=auth).json())          # only Ada's orders
    print(c.get(f"/orders/{order['id']}", headers=auth).json())
