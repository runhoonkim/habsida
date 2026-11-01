import httpx

response = httpx.get("https://jsonplaceholder.typicode.com/users/1")

print(response.status_code)
data = response.json()
print(data["name"])

import json
print(json.dumps(data, indent=2))
