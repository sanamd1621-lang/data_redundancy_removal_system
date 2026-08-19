import requests

BASE_URL = "http://localhost:5000/api/v1"

# 1. Create & Encrypt
payload = {
    "username": "alice",
    "capability_code": "CAP-QUERY-USER-READ"
}

response = requests.post(f"{BASE_URL}/user", json=payload)
data = response.json()
print("--- POST RESPONSE (Saved to DB) ---")
print(data)

# 2. Retrieve & Decrypt from DB using the returned ID
if "id" in data:
    user_id = data["id"]
    decrypt_response = requests.get(f"{BASE_URL}/user/decrypt/{user_id}")
    print("\n--- GET DECRYPTED RESPONSE (Read from DB) ---")
    print(decrypt_response.json())