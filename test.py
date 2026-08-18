import requests

url = "http://localhost:5000/api/v1/user"
payload = {
    "username": "alice",
    "capability_code": "CAP-QUERY-USER-READ",
}

response = requests.post(url, json=payload)
print(response.json())