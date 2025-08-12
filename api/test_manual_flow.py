# test_manual_flow.py
import os
import time
import threading
import requests

TIMEOUT = 12  # seconds

# ─── Config (override via env) ─────────────────────────────────────────────
API_BASE = os.getenv("TAULAYER_API_BASE", "https://taulayer-api.onrender.com/api")
POST_URL = f"{API_BASE}/requests"
GET_URL = lambda rid: f"{API_BASE}/requests/{rid}"

API_KEY = os.getenv("TAULAYER_API_KEY", "tl_test_12345")
KNOWN_EXTERNAL_ID = os.getenv("TAULAYER_EXTERNAL_ID", "apitest_001")
# Let the test auto-discover canonical user_id if not provided
KNOWN_USER_ID = os.getenv("TAULAYER_USER_ID", None)

BASE_PAYLOAD = {
    "prompt": "How many sales did we have in 2024?",
    "priority": "medium",
}

# ─── Helpers ──────────────────────────────────────────────────────────────
def pretty(label, resp, start_ts):
    elapsed = (time.time() - start_ts) * 1000.0
    print(f"\n— {label} —  ({elapsed:.1f} ms)")
    print("Status:", getattr(resp, "status_code", "N/A"))
    try:
        print("JSON:", resp.json())
    except Exception:
        text = getattr(resp, "text", "")
        print("Text:", (text or "")[:300], "…")

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {}

def safe_request_id(resp):
    return safe_json(resp).get("request_id")

def post(json_body=None, headers=None):
    return requests.post(POST_URL, json=json_body or BASE_PAYLOAD, headers=headers or {}, timeout=TIMEOUT)

def poll_request(request_id, max_s=6, every_s=0.5):
    """Poll GET until completed/failed/suggestions, or timeout."""
    last_resp = None
    deadline = time.time() + max_s
    while time.time() < deadline:
        last_resp = requests.get(GET_URL(request_id), timeout=TIMEOUT)
        try:
            data = last_resp.json()
            if data.get("status") in ("completed", "failed", "below_threshold_suggestions_sent"):
                return last_resp, data
        except Exception:
            pass
        time.sleep(every_s)
    # return whatever we last saw
    try:
        return last_resp, last_resp.json()
    except Exception:
        return last_resp, None

def GET_request_verbose(request_id, label="GET"):
    start = time.time()
    r, data = poll_request(request_id)
    pretty(f"{label} /requests/{request_id}", r, start)
    if isinstance(data, dict) and "vector_embedding" in data:
        print("⚠️ vector_embedding leaked in GET response (should be hidden)")
    return data

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
    r = requests.get(GET_URL(request_id), timeout=TIMEOUT)
    if r.status_code == 404:
        print("✅ Request not stored in DB for error case")
    else:
        print(f"⚠️ Request unexpectedly exists in DB: {r.status_code}, {(r.text or '')[:200]}")

# ─── Identity tests ───────────────────────────────────────────────────────
def run_identity_tests():
    print("\n============== TauLayer Identity Tests (no new users) ==============")

    # 0) No identity → expect 401
    start = time.time()
    r = post(BASE_PAYLOAD, {})
    pretty("POST no identity (expect 401)", r, start)
    if r.status_code != 401:
        print("⚠️ Expected 401 Unauthorized. Got:", r.status_code)
    verify_not_in_db(safe_request_id(r))

    canonical_user_id = KNOWN_USER_ID  # may be None (we’ll auto-discover)

    # 1) Header provided_user_id → must reuse existing user (no creation)
    headers = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID}
    start = time.time()
    r = post(BASE_PAYLOAD, headers)
    pretty(f"POST header provided_user_id={KNOWN_EXTERNAL_ID}", r, start)
    rid = safe_request_id(r)
    if rid:
        detail = GET_request_verbose(rid, "GET after header provided_user_id")
        uid = extract_user_id_from_get(detail)
        canonical_user_id = assert_same_user("header provided_user_id", uid, canonical_user_id)
        note = (detail or {}).get("request_note", "") or ""
        if not any(s in note for s in ["external ID", "API-key", "internal ID"]):
            print("ℹ️ identity note not found (optional check)")

    # 2) Body metadata provided_user_id → same user
    payload = BASE_PAYLOAD.copy()
    payload["metadata"] = {"provided_user_id": KNOWN_EXTERNAL_ID}
    start = time.time()
    r = post(payload, {})
    pretty(f"POST body provided_user_id={KNOWN_EXTERNAL_ID}", r, start)
    rid = safe_request_id(r)
    if rid:
        detail = GET_request_verbose(rid, "GET after body provided_user_id")
        uid = extract_user_id_from_get(detail)
        canonical_user_id = assert_same_user("body provided_user_id", uid, canonical_user_id)

    # 3) API-key user (optional)
    if API_KEY:
        headers = {"X-API-Key": API_KEY}
        start = time.time()
        r = post(BASE_PAYLOAD, headers)
        pretty("POST with API key only", r, start)
        rid = safe_request_id(r)
        if rid:
            detail = GET_request_verbose(rid, "GET after api key only")
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("api key only", uid, canonical_user_id)

    # 4) Precedence checks
    if API_KEY:
        headers = {"X-API-Key": API_KEY, "X-Provided-User-Id": KNOWN_EXTERNAL_ID}
        start = time.time()
        r = post(BASE_PAYLOAD, headers)
        pretty("POST header + API key (header wins)", r, start)
        rid = safe_request_id(r)
        if rid:
            detail = GET_request_verbose(rid, "GET after header+apikey")
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("header + api key", uid, canonical_user_id)

        payload = BASE_PAYLOAD.copy()
        payload["metadata"] = {"provided_user_id": KNOWN_EXTERNAL_ID}
        headers = {"X-API-Key": API_KEY}
        start = time.time()
        r = post(payload, headers)
        pretty("POST body provided_user_id + API key (body wins)", r, start)
        rid = safe_request_id(r)
        if rid:
            detail = GET_request_verbose(rid, "GET after body+apikey")
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("body + api key", uid, canonical_user_id)

    # 6) Internal user_id path
    if canonical_user_id:
        payload = BASE_PAYLOAD.copy()
        payload["user_id"] = canonical_user_id
        start = time.time()
        r = post(payload, {})
        pretty("POST internal user_id (canonical)", r, start)
        rid = safe_request_id(r)
        if rid:
            detail = GET_request_verbose(rid, "GET after internal user_id")
            uid = extract_user_id_from_get(detail)
            canonical_user_id = assert_same_user("internal user_id", uid, canonical_user_id)

    # 7) Unknown internal user_id → 404, not stored
    payload = BASE_PAYLOAD.copy()
    payload["user_id"] = "00000000-0000-0000-0000-000000000000"
    start = time.time()
    r = post(payload, {})
    pretty("POST internal user_id (unknown; expect 404)", r, start)
    if r.status_code != 404:
        print("⚠️ Expected 404 for unknown user_id. Got:", r.status_code)
    verify_not_in_db(safe_request_id(r))

    print("\n============== Identity Tests Done ==============")

# ─── Suggestions-path test (threshold failure) ────────────────────────────
def run_suggestions_test():
    """
    Force thresholds to fail so we return suggestions.
    With the stub predictor: latency_ms = len(prompt)*5, complexity = len(prompt)/100.
    We'll exceed both easily with a very long prompt; using 'low' makes it stricter.
    """
    print("\n============== Suggestions Path Test ==============")
    headers = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID}
    long_prompt = "x" * 2000  # huge; guarantees fail under current stubs
    payload = {"prompt": long_prompt, "priority": "low"}

    start = time.time()
    r = post(payload, headers)
    pretty("POST long prompt to trigger suggestions", r, start)

    if r.status_code == 200:
        body = safe_json(r)
        if body.get("status") != "below_threshold_suggestions_sent":
            print(f"⚠️ Expected status below_threshold_suggestions_sent, got {body.get('status')}")
        if not body.get("suggestions"):
            print("⚠️ Expected suggestions list in POST response")
        rid = body.get("request_id")
        if rid:
            detail = GET_request_verbose(rid, "GET after suggestions")
            if not (detail or {}).get("suggestions"):
                print("⚠️ Expected suggestions persisted on the request row")
    else:
        print("⚠️ Expected 200 from POST (with suggestions), got", r.status_code)


def run_too_long_prompt_test():
    print("\n— POST too-long prompt (expect 413) —")
    headers = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID}
    payload = {
        "prompt": "x" * (12000 + 50),  # just over the limit
        "priority": "low",
    }
    start = time.time()
    r = requests.post(POST_URL, json=payload, headers=headers, timeout=TIMEOUT)
    pretty("POST too-long prompt", r, start)
    if r.status_code != 413:
        print(f"⚠️ Expected 413, got {r.status_code}")
    # ensure nothing was stored
    rid = None
    if r.headers.get("content-type","").startswith("application/json"):
        rid = r.json().get("request_id")
    verify_not_in_db(rid)

# ─── 422 invalid payload test ─────────────────────────────────────────────
def run_422_test():
    print("\n============== 422 Validation Test ==============")
    headers = {"Content-Type": "application/json"}
    bad_payload = {"priority": "medium"}  # missing 'prompt'
    start = time.time()
    r = requests.post(POST_URL, json=bad_payload, headers=headers, timeout=TIMEOUT)
    pretty("POST missing prompt (expect 422)", r, start)
    if r.status_code != 422:
        print(f"⚠️ Expected 422, got {r.status_code}")
    else:
        err = safe_json(r)
        if err.get("error") != "Invalid request payload":
            print("ℹ️ 422 body didn't match expected error shape (this is OK if handler changed)")

# ─── Type-1 Fault-injection (503/504) ────────────────────────────────────
def run_type1_fault_tests():
    print("\n============== Type-1 Fault Injection (503/504) ==============")
    headers = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID}

    # 200 sanity
    start = time.time()
    r = post(BASE_PAYLOAD, headers)
    pretty("POST normal (expect 200)", r, start)

    # 504 simulated timeout
    headers_timeout = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID, "X-Force-DB-Timeout": "1"}
    start = time.time()
    r = post(BASE_PAYLOAD, headers_timeout)
    pretty("POST simulated DB timeout (expect 504)", r, start)
    if r.status_code != 504:
        print(f"ℹ️ Expected 504, got {r.status_code} (DEBUG may be disabled or patch not deployed)")

    # 503 simulated unavailable
    headers_unavail = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID, "X-Force-DB-Unavailable": "1"}
    start = time.time()
    r = post(BASE_PAYLOAD, headers_unavail)
    pretty("POST simulated DB unavailable (expect 503)", r, start)
    if r.status_code != 503:
        print(f"ℹ️ Expected 503, got {r.status_code} (DEBUG may be disabled or patch not deployed)")

    print("\n============== Fault Injection Tests Done ==============")

# ─── Optional: simple concurrency check ───────────────────────────────────
def run_concurrency_check(n=8):
    print("\n============== Concurrency Check ==============")
    headers = {"X-Provided-User-Id": KNOWN_EXTERNAL_ID}
    rids = []
    lock = threading.Lock()

    def worker():
        try:
            r = post(BASE_PAYLOAD, headers)
            if r.status_code == 200:
                rid = safe_request_id(r)
                with lock:
                    rids.append(rid)
        except Exception as e:
            print("thread error:", e)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    users = []
    for rid in rids:
        detail = GET_request_verbose(rid, "GET (concurrency)")
        uid = extract_user_id_from_get(detail)
        users.append(uid)

    uniq = list({u for u in users if u})
    if len(uniq) == 1:
        print(f"✅ All {len(users)} requests resolved to the same user_id: {uniq[0]}")
    else:
        print(f"⚠️ Mismatch user_ids under concurrency: {uniq}")

def run_all():
    run_identity_tests()
    run_suggestions_test()
    run_422_test()
    run_type1_fault_tests()
    run_too_long_prompt_test()
    # run_concurrency_check(8)  # uncomment to exercise parallel posts

if __name__ == "__main__":
    run_all()
