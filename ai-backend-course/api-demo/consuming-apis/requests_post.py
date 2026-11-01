import requests

new_post = {
    "title": "First order", 
    "body": "Two units", 
    "userId": 1
}

response = requests.post(
    "https://jsonplaceholder.typicode.com/posts",
    json=new_post,
)

print(response.status_code)   # 201 Created
print(response.json()["id"])  # the id the server assigned