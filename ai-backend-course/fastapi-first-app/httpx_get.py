import httpx
import json

URL = "http://127.0.0.1:8000"

def print_response(response) -> None:
    print("status code:", response.status_code)
    print("url:", response.url)
    print("headers:", json.dumps(dict(response.headers), indent=2))
    print("body:", json.dumps(response.json(), indent=2))

    return None

# @app.get("/")
# response = httpx.get(URL)
# print_response(response)

# @app.get("/orders/{order_id}")
# response = httpx.get(f"{URL}/orders/42")
# print_response(response)

# @app.get("/orders/status/{status}")
# response = httpx.get(f"{URL}/orders/status/invalid")
# print_response(response)

# @app.get("/orders")
# response = httpx.get(f"{URL}/orders")
# print_response(response)

# @app.get("/users/{user_id}/orders")
response = httpx.get(f"{URL}/users/1/orders") # {"user_id":1,"skip":0,"limit":10}
response = httpx.get(f"{URL}/users/7/orders?skip=5&limit=7") # {"user_id":7,"skip":5,"limit":7}
print_response(response)