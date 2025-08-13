# test_threshold_suggestions.py
import os, time, requests

TIMEOUT = int(os.getenv("TAULAYER_TIMEOUT", "12"))
API_BASE = os.getenv("TAULAYER_API_BASE", "https://taulayer-api.onrender.com/api")
POST_URL = f"{API_BASE}/requests"
GET_URL  = lambda rid: f"{API_BASE}/requests/{rid}"
PROVIDED_USER_ID = os.getenv("TAULAYER_USER_ID", "apitest_001")

def pretty(label, resp, t0):
    ms = (time.time() - t0) * 1000
    print(f"\n— {label} — ({ms:.1f} ms)\nStatus:", resp.status_code)
    try:
        print("JSON:", resp.json())
    except Exception:
        print("Text:", resp.text[:400], "…")

def post(payload, headers):
    return requests.post(POST_URL, json=payload, headers=headers, timeout=TIMEOUT)

def get_req(rid):
    time.sleep(1.5)
    return requests.get(GET_URL(rid), timeout=TIMEOUT)

def _build_text(n: int) -> str:
    seed = (
        "Please generate a comprehensive, unfiltered report across all data dimensions, "
        "including trends, anomalies, and recommended actions. "
    )
    return (seed * (n // len(seed) + 1))[:n]

def run():
    headers = {"X-Provided-User-Id": PROVIDED_USER_ID}

    # A) sanity pass (should execute)
    short = {"prompt": "Quick summary of Q1 revenue by region?", "priority": "medium"}
    t0 = time.time(); r = post(short, headers); pretty("PASS sanity", r, t0)
    assert r.status_code == 200 and r.json().get("status") == "sent_to_execution"

    # B) fail path: ramp prompt size until suggestions trigger (stays well under 413 cap)
    for size in (600, 900, 1200, 1600, 2200, 3000, 3600):
        fail_payload = {"prompt": _build_text(size), "priority": "low"}  # "low" makes failure more likely
        t0 = time.time(); r = post(fail_payload, headers); pretty(f"FAIL probe size={size}", r, t0)

        # If your server-side 413 guard trips, don't keep increasing
        if r.status_code == 413:
            print("Hit 413 guard — prompt exceeded max length. Reduce size and re-run.")
            return

        # Success: suggestions were sent instead of execution
        if r.status_code == 200 and r.json().get("status") == "below_threshold_suggestions_sent":
            body = r.json()
            suggestions = body.get("suggestions") or []
            assert isinstance(suggestions, list) and len(suggestions) > 0, "Expected non-empty suggestions on POST"

            rid = body.get("request_id"); assert rid, "Expected request_id on fail path"

            # GET should persist the fail status + suggestions (often as strings from DB)
            t0 = time.time(); g = get_req(rid); pretty(f"GET {rid}", g, t0)
            assert g.status_code == 200
            gbody = g.json()
            assert gbody.get("status") == "below_threshold_suggestions_sent"
            stored = gbody.get("suggestions") or []
            assert isinstance(stored, list), "Expected list of suggestions in GET response"

            # Helpful visibility when DB stores strings
            if stored and isinstance(stored[0], str):
                print("✅ Suggestions persisted as strings:", stored)

            print(f"\n✅ Threshold fail → suggestions verified at size {size} chars (POST & GET).")
            return

    # If we get here, we couldn't trigger the suggestions flow
    raise AssertionError(
        "Could not trigger suggestions with the tested sizes. "
        "Consider slightly larger sizes (< your 413 cap) or lowering thresholds for this test."
    )

if __name__ == "__main__":
    run()
