import requests

# ─── Config ───────────────────────────────────────────────────────────────
API_URL = "https://taulayer-api.onrender.com/api/requests"  # Render deployment
API_KEY = None  # Replace with your actual key if needed, e.g., "tl_abc123xyz"

# ─── Headers ──────────────────────────────────────────────────────────────
headers = {}
if API_KEY:
    headers["X-API-Key"] = API_KEY

# ─── Payload ──────────────────────────────────────────────────────────────
payload = {
    "prompt": "How many sales did we have last month?",
    "priority": "medium"
}

# ─── Request ──────────────────────────────────────────────────────────────
response = requests.post(API_URL, json=payload, headers=headers)

print("Response Status:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Response Text:", response.text)
