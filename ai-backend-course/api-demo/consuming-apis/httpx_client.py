import httpx

with httpx.Client(
    base_url="https://jsonplaceholder.typicode.com",
    headers={"Accept": "application/json"},
    timeout=10.0,
) as client:
    
    user = client.get("/users/1").json()
    posts = client.get("/posts", params={"userId": 1}).json()
    print(user["name"], "wrote", len(posts), "posts")