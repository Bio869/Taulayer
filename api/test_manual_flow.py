import requests
import time

# ─── Config ───────────────────────────────────────────────────────────────
API_BASE = "https://taulayer-api.onrender.com/api"
POST_URL = f"{API_BASE}/requests"
GET_URL = lambda rid: f"{API_BASE}/requests/{rid}"

# Set these to match the ONE user you inserted in SQL
API_KEY = "tl_test_12345"           # plain key you inserted (will be hashed server-side)
KNOWN_EXTERNAL_ID = "apitest_001"   # provided_user_id you inserted
KNOWN_USER_ID = None                # optional: set to the UUID returned by SQL (if known)

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
    try:
        return r.json()
    except Exception:
        return None

def POST_case(label, payload=None, headers=None):
    payload = payload or BASE_PAYLOAD.copy()
    headers = headers or {}
    start = time.time()
    r = requests.post(POST_URL, json=payload, headers=headers)
    pretty(label, r, start)
    try:
        data = r.json()
        return r.status_code, data.get("request_id")
    except Exception:
        return r.status_code, None

def extract_user_id_from_get(json_obj):
    if isinstance(json_obj, dict):
        return json_obj.get("user_id")
    return None

def assert_same_user(label, got_user_id, expected_user_id):
    if not expected_user_id:
        print(f"[{label}] discovered user_id = {got_user_id}")
        return got_user_id
    if got_user_id != expected_user_id:
        print(f"⚠️ [{label}] MISMATCH: got {got_user_id} but expected {expected_user_id}")
    else:
        print(f"✅ [{label}] user_id matches expected")
    return expected_user_id

def verify_not_in_db(request_id):
    if not request_id:
        print("No request_id returned — as expected for error case")
        return
    # GET should 404 if request was never stored
    r = requests.get(GET_URL(request_id))
    if r.status_code == 404:
        print("✅ Request not stored in DB for error case")
    else:
        print(f"⚠️ Request unexpectedly exists in DB: {r.status_code}, {r.text}")

def run_tests():
    print("\n============== TauLayer Identity Tests (no new users) ==============")

    # 0) No identity → expect 401
    status, rid = POST_case("POST no identity (expect 401)")
    if status != 401:
        print("⚠️ Expected 401 Unauthorized here. Got:", status)
    verify_not_in_db(rid)

    # Will store the canonical user_id we observe the first time
    canonical_user_id = KNOWN_USER_ID

    # 1) Header provided_user_id → must reuse existing user (no creation)
    headers = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID}
    status, rid = POST_case(f"POST header provided_user_id={KNOWN_EXTERNAL_ID}", headers=headers)
    if rid:
        detail = GET_request(rid)
        uid = extract_user_id_from_get(detail)
        canonical_user_id = assert_same_user("header provided_user_id", uid, canonical_user_id)

    # 2) Body metadata provided_user_id with the SAME external id → must resolve to same user
    payload = BASE_PAYLOAD.copy()
    payload["metadata"] = {"provided_user_id": KNOWN_EXTERNAL_ID}
    status, rid = POST_case(f"POST body provided_user_id={KNOWN_EXTERNAL_ID}", payload=payload)
    if rid:
        detail = GET_request(rid)
        uid = extract_user_id_from_get(detail)
        canonical_user_id = assert_same_user("body provided_user_id", uid, canonical_user_id)

    # 3) API-key user → must resolve to same user
    if API_KEY:
        headers = {"X-API-Key": API_KEY}
        status, rid = POST_case("POST with API key only", headers=headers)
        if rid:
            detail = GET_request(rid)
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("api key only", uid, canonical_user_id)
    else:
        print("\n(Skipping API key test — set API_KEY to enable)")

    # 4) Precedence check: header + API key → header should win (same canonical user)
    if API_KEY:
        headers = {"X-API-Key": API_KEY, "X-Provided-User-Id": KNOWN_EXTERNAL_ID}
        status, rid = POST_case("POST header + API key (header wins)", headers=headers)
        if rid:
            detail = GET_request(rid)
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("header + api key", uid, canonical_user_id)

    # 5) Precedence check: body provided_user_id + API key → body should win over API key
    if API_KEY:
        payload = BASE_PAYLOAD.copy()
        payload["metadata"] = {"provided_user_id": KNOWN_EXTERNAL_ID}
        headers = {"X-API-Key": API_KEY}
        status, rid = POST_case("POST body provided_user_id + API key (body wins)", payload=payload, headers=headers)
        if rid:
            detail = GET_request(rid)
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("body + api key", uid, canonical_user_id)

    # 6) Internal user_id path: use the discovered canonical_user_id (never creates)
    if canonical_user_id:
        payload = BASE_PAYLOAD.copy()
        payload["user_id"] = canonical_user_id
        status, rid = POST_case("POST internal user_id (canonical)", payload=payload)
        if rid:
            detail = GET_request(rid)
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("internal user_id", uid, canonical_user_id)
    else:
        print("\n⚠️ Could not determine canonical user_id; skipping internal user_id test.")

    # 7) Internal user_id unknown → expect 404 (no creation)
    payload = BASE_PAYLOAD.copy()
    payload["user_id"] = "00000000-0000-0000-0000-000000000000"
    status, rid = POST_case("POST internal user_id (unknown; expect 404)", payload=payload)
    if status != 404:
        print("⚠️ Expected 404 for unknown user_id. Got:", status)
    verify_not_in_db(rid)   

    print("\n============== Done ==============")
    if canonical_user_id:
        print(f"Canonical user_id confirmed: {canonical_user_id}")

if __name__ == "__main__":
    run_tests()
