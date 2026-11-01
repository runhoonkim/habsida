# import httpx

# with httpx.Client(base_url="http://127.0.0.1:8000") as client:
#     created = client.post("/orders", json={"user_id": 7, "product_id": 3, "quantity": 2}).json()
#     order_id = created["id"]
#     client.patch(f"/orders/{order_id}", json={"status": "shipped"})
#     print(client.get(f"/orders/{order_id}").json())
#     client.delete(f"/orders/{order_id}")

import os
from dotenv import load_dotenv
import json

load_dotenv()
api_key_str = os.environ["VALID_API_KEYS"]
valid_api_keys = json.loads(api_key_str)
