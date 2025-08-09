import requests
import time
import uuid

# ─── Config ───────────────────────────────────────────────────────────────
API_BASE = "https://taulayer-api.onrender.com/api"
POST_URL = f"{API_BASE}/requests"
GET_URL = lambda rid: f"{API_BASE}/requests/{rid}"

# ⚠️ Set this to the ACTUAL API key (plain string like "tl_abc123")
API_KEY = None

# Provided by you (internal UUID for users.id)
KNOWN_USER_ID = "685f529c-38ea-4738-a182-accb4950fe03"

# This should 404
UNKNOWN_USER_ID = "00000000-0000-0000-0000-000000000000"

# Provided by you (external id / provided_user_id)
EXTERNAL_ID = "anonymous_685f529c"

BASE_PAYLOAD = {
    "prompt": "How many sales did we have in 2024?",
    "priority": "medium",
}

def pretty(label, resp, start_ts):
    elapsed = (time.time() - start_ts) * 1000.0
    print(f"\n— {label} —  ({elapsed:.1f} ms)")
    print("Status:", resp.status_code)
    try:
        print("JSON:", resp.json())
    except Exception:
        print("Text:", resp.text)

def GET_request(request_id):
    # Give the background task a moment
    time.sleep(2)
    start = time.time()
    r = requests.get(GET_URL(request_id))
    pretty(f"GET /requests/{request_id}", r, start)

def POST_case(label, payload=None, headers=None):
    payload = payload or BASE_PAYLOAD.copy()
    headers = headers or {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    start = time.time()
    r = requests.post(POST_URL, json=payload, headers=headers)
    pretty(label, r, start)
    try:
        data = r.json()
        return r.status_code, data.get("request_id")
    except Exception:
        return r.status_code, None

def run_tests():
    print("\n============== TauLayer Manual Tests ==============")

    # 0) No identity at all → expect 401
    status, rid = POST_case("POST no identity (expect 401)")
    if status != 401:
        print("⚠️ Expected 401 Unauthorized here. Got:", status)

    # 1) Header provided_user_id → upsert/reuse (should reuse if already exists)
    headers = {"X-Provided-User-Id": EXTERNAL_ID}
    status, rid = POST_case(f"POST header provided_user_id={EXTERNAL_ID}", headers=headers)
    if rid:
        GET_request(rid)

    # 2) Body metadata provided_user_id with the SAME external id → must reuse same user
    payload = BASE_PAYLOAD.copy()
    payload["metadata"] = {"provided_user_id": EXTERNAL_ID}
    status, rid = POST_case(f"POST body provided_user_id={EXTERNAL_ID}", payload=payload)
    if rid:
        GET_request(rid)

    # 3) API-key user (only runs if API_KEY is set to a real key)
    if API_KEY:
        status, rid = POST_case("POST with API key only")
        if rid:
            GET_request(rid)
    else:
        print("\n(Skipping API key test — set API_KEY to enable)")

    # 4) Internal user_id happy path (uses your KNOWN_USER_ID)
    if KNOWN_USER_ID:
        payload = BASE_PAYLOAD.copy()
        payload["user_id"] = KNOWN_USER_ID
        status, rid = POST_case("POST internal user_id (known)", payload=payload)
        if rid:
            GET_request(rid)
    else:
        print("\n(Skipping internal known user_id test — set KNOWN_USER_ID to enable)")

    # 5) Internal user_id unknown → expect 404
    payload = BASE_PAYLOAD.copy()
    payload["user_id"] = UNKNOWN_USER_ID
    status, rid = POST_case("POST internal user_id (unknown; expect 404)", payload=payload)
    if status != 404:
        print("⚠️ Expected 404 for unknown user_id. Got:", status)

    print("\n============== Done ==============")

if __name__ == "__main__":
    run_tests()
