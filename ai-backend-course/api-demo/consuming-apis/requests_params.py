import requests

response = requests.get(
    "https://jsonplaceholder.typicode.com/posts",
    params={"userId": 1,
            "id": 1},
)

print(response.url) # https://jsonplaceholder.typicode.com/posts?userId=1&id=1
posts = response.json()
print(f"User 1 has {len(posts)} posts") 

import json
# print(json.dumps(posts, indent=2))