# test_queue_and_schedule.py
import os
import time
import json
import requests
from datetime import datetime, timedelta, timezone

TIMEOUT_S = int(os.getenv("TAULAYER_TIMEOUT", "20"))

API_BASE   = os.getenv("TAULAYER_API_BASE", "https://taulayer-api.onrender.com/api")
POST_URL   = f"{API_BASE}/requests"
GET_URL    = lambda rid: f"{API_BASE}/requests/{rid}"
PROVIDED_USER_ID = os.getenv("TAULAYER_EXTERNAL_ID", "apitest_001")

# --- Optional Supabase direct verification ---
SB_URL       = os.getenv("SUPABASE_URL")              # e.g. https://<project>.supabase.co
SB_SERVICE   = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # service key preferred
SB_SCHEMA    = os.getenv("SUPABASE_SCHEMA", "public")

def _sb_headers():
    return {
        "apikey": SB_SERVICE,
        "Authorization": f"Bearer {SB_SERVICE}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def _sb_table_url(table):
    # REST endpoint: /rest/v1/<schema>_<table> OR if table in public, just /rest/v1/<table>
    # Supabase exposes schema-qualified via `rpc`, but for tables it’s /rest/v1/<table>.
    return f"{SB_URL}/rest/v1/{table}"

def _sb_get(table, params):
    if not (SB_URL and SB_SERVICE):
        return None, "SKIPPED (no Supabase env provided)"
    r = requests.get(_sb_table_url(table), params=params, headers=_sb_headers(), timeout=TIMEOUT_S)
    try:
        return r.json(), None
    except Exception:
        return None, f"bad response: status={r.status_code} body={(r.text or '')[:200]}"

# --------------- Helpers -----------------
def _utcnow():
    return datetime.now(timezone.utc)

def _iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def _post(payload, headers):
    return requests.post(POST_URL, json=payload, headers=headers, timeout=TIMEOUT_S)

def _poll_get(rid, max_s=12, every_s=0.5):
    deadline = time.time() + max_s
    last = None
    while time.time() < deadline:
        r = requests.get(GET_URL(rid), timeout=TIMEOUT_S)
        try:
            data = r.json()
            if data.get("status") in ("completed", "failed", "below_threshold_suggestions_sent", "sent_to_execution"):
                return r, data
            last = (r, data)
        except Exception:
            last = (r, None)
        time.sleep(every_s)
    return last if last else (None, None)

def _print(label, obj):
    print(f"\n— {label} —")
    if isinstance(obj, requests.Response):
        print("Status:", obj.status_code)
        try:
            print("JSON:", json.dumps(obj.json(), indent=2))
        except Exception:
            print("Text:", (obj.text or "")[:400])
    else:
        print(obj)

# --------------- Tests -----------------

def test_queue_asap():
    """
    Trigger the durable ASAP queue (enqueue_job) by making latency_estimate > background_max_latency_ms
    while still passing thresholds (use priority='high').
    """
    headers = {"X-Provided-User-Id": PROVIDED_USER_ID}
    # make it long enough to estimate > ~2000ms, but keep priority 'high' to pass thresholds
    prompt = "Analyze Q1 vs Q2 revenue drivers and cohort retention." * 80
    payload = {"prompt": prompt, "priority": "high"}

    r = _post(payload, headers); _print("POST queue ASAP", r)
    assert r.status_code == 200, f"expected 200; got {r.status_code}"
    body = r.json()
    assert body.get("status") == "sent_to_execution"
    rid = body.get("request_id"); assert rid, "missing request_id"

    # It should either quickly complete (your dummy background) OR remain sent_to_execution briefly.
    g, data = _poll_get(rid, max_s=15)
    _print(f"GET {rid}", g)
    assert g is not None and g.status_code == 200
    final = data.get("status")
    assert final in ("completed", "sent_to_execution"), f"unexpected final status: {final}"

    # Optional: verify a jobs row was created for ASAP run
    jobs, err = _sb_get("jobs", {"requests_id": f"eq.{rid}"})
    if err:
        print("🔸 jobs check:", err)
    else:
        # If your code enqueues ASAP jobs only when latency > cutoff:
        # - For ASAP path, you should see a row with run_at NULL (or now-ish), depending on implementation.
        print("jobs rows for request:", jobs)
        assert isinstance(jobs, list)
        assert len(jobs) >= 1, "expected at least one jobs row for ASAP queue"

def test_schedule_future_with_notify():
    """
    Ask to schedule in the future + notify via email.
    Server should:
      - return sent_to_execution with estimated_completion_time == scheduled_for
      - create a durable job with run_at=scheduled_for
      - persist notify_email (either column or request_note fallback)
    """
    headers = {"X-Provided-User-Id": PROVIDED_USER_ID}
    scheduled_for = _utcnow() + timedelta(minutes=5)
    notify_email = "qa+schedule@example.com"

    payload = {
        "prompt": "Full company KPI deep-dive across revenue, churn, cohorts, and CAC/LTV.",
        "priority": "high",
        "scheduled_for": _iso(scheduled_for),  # ISO in UTC
        "metadata": {"notify_email": notify_email},
    }

    r = _post(payload, headers); _print("POST schedule future", r)
    assert r.status_code == 200, f"expected 200; got {r.status_code}"
    body = r.json()
    assert body.get("status") == "sent_to_execution"
    rid = body.get("request_id"); assert rid, "missing request_id"

    # server echoes estimated_completion_time (should match scheduled_for closely)
    eta = body.get("estimated_completion_time"); assert eta, "missing estimated_completion_time"
    print("scheduled_for (client):", _iso(scheduled_for))
    print("estimated_completion_time (server):", eta)
    # allow a few seconds wiggle
    assert eta.startswith(_iso(scheduled_for)[:16]), "ETA not aligned with scheduled_for (minute-level check)"

    # GET should keep it in sent_to_execution (not executed yet)
    g, data = _poll_get(rid, max_s=5)  # it should *not* complete immediately
    _print(f"GET {rid}", g)
    assert g is not None and g.status_code == 200
    assert data.get("status") == "sent_to_execution", "scheduled job should not auto-complete now"

    # Optional DB checks (requires Supabase creds)
    # 1) jobs exists with run_at ~= scheduled_for
    jobs, err = _sb_get("jobs", {"requests_id": f"eq.{rid}"})
    if err:
        print("🔸 jobs check:", err)
    else:
        print("jobs rows for scheduled request:", jobs)
        assert isinstance(jobs, list) and len(jobs) >= 1, "expected a jobs row for scheduled run"
        # check run_at ~ scheduled_for (minute-level)
        job = jobs[0]
        run_at = job.get("run_at") or job.get("scheduled_for")  # depending on your schema
        assert run_at, "job.run_at not set"
        print("job.run_at:", run_at)
        assert run_at.startswith(_iso(scheduled_for)[:16])

    # 2) requests row persisted notify_email (column or note)
    reqs, err2 = _sb_get("requests", {"id": f"eq.{rid}", "select": "id,notify_email,request_note,scheduled_for"})
    if err2:
        print("🔸 requests check:", err2)
    else:
        print("requests row:", reqs)
        assert isinstance(reqs, list) and len(reqs) == 1
        row = reqs[0]
        # scheduled_for stored?
        stored_sched = row.get("scheduled_for")
        assert stored_sched and stored_sched.startswith(_iso(scheduled_for)[:16]), "scheduled_for not persisted correctly"
        # notify email either in column or the note fallback
        if row.get("notify_email"):
            assert row["notify_email"] == notify_email
        else:
            note = (row.get("request_note") or "")
            assert f"notify:{notify_email}" in note, "notify email not present in request_note fallback"

if __name__ == "__main__":
    print("Running queue & schedule tests…")
    test_queue_asap()
    test_schedule_future_with_notify()
    print("\n✅ queue & schedule tests completed")
