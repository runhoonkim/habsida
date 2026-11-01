import requests

response = requests.get("https://jsonplaceholder.typicode.com/users/1")


print(response.status_code)        # 200
print(response.headers["Content-Type"])  # application/json; charset=utf-8
data = response.json()             # parse the JSON body into a Python dict
print(data["name"], data["email"])

import json
print(json.dumps(dict(response.headers), indent=2))