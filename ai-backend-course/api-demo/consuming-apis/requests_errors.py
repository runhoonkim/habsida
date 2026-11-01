import requests

headers = {"Authorization": "Bearer demo-token"}
response = requests.get("https://jsonplaceholder.typicode.com/users/999", headers=headers)

print(type(response.status_code))

if response.status_code == 404:
    print("User not found")

else:
    response.raise_for_status()   # raise an exception on any 4xx/5xx
    print(response.json())