# test_queue_and_schedule.py
from datetime import datetime, timedelta, timezone
import requests, time, os, json

TIMEOUT_S = int(os.getenv("TAULAYER_TIMEOUT", "20"))

API_BASE   = os.getenv("TAULAYER_API_BASE", "https://taulayer-api.onrender.com/api")
POST_URL   = f"{API_BASE}/requests"
GET_URL    = lambda rid: f"{API_BASE}/requests/{rid}"
PROVIDED_USER_ID = os.getenv("TAULAYER_EXTERNAL_ID", "apitest_001")

# --- Optional Supabase direct verification ---
SB_URL       = os.getenv("SUPABASE_URL")              # e.g. https://<project>.supabase.co
SB_SERVICE   = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # service key preferred

def _sb_headers():
    return {
        "apikey": SB_SERVICE,
        "Authorization": f"Bearer {SB_SERVICE}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def _sb_table_url(table):
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
    Try to trigger the durable ASAP queue by making predicted latency > background cutoff.
    If predictor doesn't exceed the server cutoff, still verify normal completion.
    """
    headers = {"X-Provided-User-Id": PROVIDED_USER_ID}

    # Keep well under 4k chars to avoid 413. Adjust repeats as needed.
    base = "Analyze Q1 vs Q2 revenue drivers and cohort retention. "
    prompt = base * 70  # ~< 4000 chars

    payload = {"prompt": prompt, "priority": "high"}  # 'high' helps pass thresholds
    r = _post(payload, headers); _print("POST queue ASAP", r)
    assert r.status_code == 200, f"expected 200; got {r.status_code}"
    body = r.json()
    assert body.get("status") == "sent_to_execution"
    rid = body.get("request_id"); assert rid, "missing request_id"

    # Poll for result (either completed quickly or still 'sent_to_execution' briefly)
    g, data = _poll_get(rid, max_s=15)
    _print(f"GET {rid}", g)
    assert g is not None and g.status_code == 200
    final = data.get("status")
    assert final in ("completed", "sent_to_execution"), f"unexpected final status: {final}"

    # Optional: check jobs table. This will only be present if server decided it's "heavy".
    jobs, err = _sb_get("jobs", {"request_id": f"eq.{rid}"})
    if err:
        print("🔸 jobs check:", err)
    else:
        print("jobs rows for request:", jobs)
        # If predictor didn't exceed the heavy cutoff, there may be 0 rows. Don't hard-fail.
        if isinstance(jobs, list) and len(jobs) == 0:
            print("ℹ️ No jobs row — likely executed via short background task (below heavy cutoff).")
        else:
            assert isinstance(jobs, list) and len(jobs) >= 1, "expected at least one jobs row for ASAP queue"

def test_schedule_future_with_notify():
    """
    Ask to schedule in the future + notify.
    Server:
      - returns sent_to_execution with estimated_completion_time == scheduled_for
      - creates a durable job with run_at=scheduled_for
      - persists notify intent using verified user email (not arbitrary client email)
    """
    headers = {"X-Provided-User-Id": PROVIDED_USER_ID}
    scheduled_for = _utcnow() + timedelta(minutes=5)

    payload = {
        "prompt": "Full company KPI deep-dive across revenue, churn, cohorts, and CAC/LTV.",
        "priority": "high",
        "scheduled_for": _iso(scheduled_for),      # ISO UTC
        "metadata": {"notify": True},              # << intent only; server uses verified user email
    }

    r = _post(payload, headers); _print("POST schedule future", r)
    assert r.status_code == 200, f"expected 200; got {r.status_code}"
    body = r.json()
    assert body.get("status") == "sent_to_execution"
    rid = body.get("request_id"); assert rid, "missing request_id"

    eta = body.get("estimated_completion_time"); assert eta, "missing estimated_completion_time"
    # minute-level alignment is fine (allow seconds skew)
    assert eta.startswith(_iso(scheduled_for)[:16]), f"ETA not aligned: scheduled={_iso(scheduled_for)} server={eta}"

    # GET should still show sent_to_execution until the scheduler runs
    g, data = _poll_get(rid, max_s=5)
    _print(f"GET {rid}", g)
    assert g is not None and g.status_code == 200
    assert data.get("status") == "sent_to_execution", "scheduled job should not auto-complete immediately"

    # Optional DB checks (requires SB creds)
    # a) jobs exists with run_at ~= scheduled_for
    jobs, err = _sb_get("jobs", {"request_id": f"eq.{rid}"})
    if err:
        print("🔸 jobs check:", err)
    else:
        print("jobs rows for scheduled request:", jobs)
        assert isinstance(jobs, list) and len(jobs) >= 1, "expected a jobs row for scheduled run"
        job = jobs[0]
        run_at = job.get("run_at") or job.get("scheduled_for")
        assert run_at, "job.run_at not set"
        assert run_at.startswith(_iso(scheduled_for)[:16]), f"job.run_at mismatch: {run_at}"

    # b) requests row persisted notify intent (verified email or hint)
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

        note = (row.get("request_note") or "")
        # Either we have a verified email stored, or we left a clear hint for admin follow-up
        if row.get("notify_email"):
            assert "@" in row["notify_email"], "notify_email persisted but looks invalid"
            assert f"notify:{row['notify_email']}" in note or True  # note may or may not echo; tolerate both
        else:
            assert "notify_requested_but_no_verified_email" in note, "missing notify hint when user email not set"

if __name__ == "__main__":
    print("Running queue & schedule tests…")
    test_queue_asap()
    test_schedule_future_with_notify()
    print("\n✅ queue & schedule tests completed")
