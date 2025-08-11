# test_threshold_suggestions.py
import os, time, requests

TIMEOUT = 12
API_BASE = os.getenv("TAULAYER_API_BASE", "https://taulayer-api.onrender.com/api")
POST_URL = f"{API_BASE}/requests"
GET_URL  = lambda rid: f"{API_BASE}/requests/{rid}"
PROVIDED_USER_ID = os.getenv("TAULAYER_USER_ID", "apitest_001")

def pretty(label, resp, t0):
    ms = (time.time() - t0) * 1000
    print(f"\n— {label} — ({ms:.1f} ms)\nStatus:", resp.status_code)
    try: print("JSON:", resp.json())
    except: print("Text:", resp.text[:400], "…")

def post(payload, headers):
    return requests.post(POST_URL, json=payload, headers=headers, timeout=TIMEOUT)

def get_req(rid):
    time.sleep(1.5)
    return requests.get(GET_URL(rid), timeout=TIMEOUT)

def run():
    headers = {"X-Provided-User-Id": PROVIDED_USER_ID}

    # A) sanity pass (should execute)
    short = {"prompt": "Quick summary of Q1 revenue by region?", "priority": "medium"}
    t0 = time.time(); r = post(short, headers); pretty("PASS sanity", r, t0)
    assert r.status_code == 200 and r.json().get("status") == "sent_to_execution"

    # B) fail case (medium thresholds: len(prompt)*5 > 800 and/or len/100 > 0.6)
    long_prompt = "x" * 250  # definitely over both latency/complexity thresholds
    fail_payload = {"prompt": long_prompt, "priority": "medium"}
    t0 = time.time(); r = post(fail_payload, headers); pretty("FAIL path (expect suggestions)", r, t0)
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "below_threshold_suggestions_sent"
    suggestions = body.get("suggestions") or []
    assert isinstance(suggestions, list) and len(suggestions) > 0, "Expected suggestion objects on POST"

    rid = body.get("request_id"); assert rid, "Expected request_id on fail path"

    # GET should persist the fail status + suggestions list (stored as strings)
    t0 = time.time(); g = get_req(rid); pretty(f"GET {rid}", g, t0)
    assert g.status_code == 200
    gbody = g.json()
    assert gbody.get("status") == "below_threshold_suggestions_sent"
    stored = gbody.get("suggestions") or []
    assert isinstance(stored, list), "Expected list of suggestions in GET response"
    # Typically these are strings from your DB
    if stored and isinstance(stored[0], str):
        print("✅ Suggestions persisted as strings:", stored)

    print("\n✅ Threshold fail → suggestions verified (POST & GET).")

if __name__ == "__main__":
    run()
