# test_parallel_requests.py
import os, time, threading, requests
from collections import defaultdict

TIMEOUT = 12
API_BASE = os.getenv("TAULAYER_API_BASE", "https://taulayer-api.onrender.com/api")
POST_URL = f"{API_BASE}/requests"
GET_URL  = lambda rid: f"{API_BASE}/requests/{rid}"

# 12 distinct English prompts (one per user)
DEFAULT_USERS = [
    ("apitest_par_01", "Summarize Q1 revenue by region."),
    ("apitest_par_02", "List the top 5 customer support issues from last month."),
    ("apitest_par_03", "Compare weekly active users for the last 8 weeks."),
    ("apitest_par_04", "Find anomalies in daily signups during July."),
    ("apitest_par_05", "Forecast paid ad spend for next quarter."),
    ("apitest_par_06", "Extract action items from the leadership meeting notes."),
    ("apitest_par_07", "Compute conversion rates by acquisition channel."),
    ("apitest_par_08", "Rank products by gross margin and units sold."),
    ("apitest_par_09", "Identify churn-risk segments among paying customers."),
    ("apitest_par_10", "Outline steps to migrate the database with minimal downtime."),
    ("apitest_par_11", "Draft a weekly status update for stakeholders."),
    ("apitest_par_12", "Generate a release QA checklist for the mobile app."),
]

# Optional: override users via env (CSV). Prompts auto-generate for you.
if os.getenv("TAULAYER_USERS"):
    ids = [u.strip() for u in os.getenv("TAULAYER_USERS").split(",") if u.strip()]
    DEFAULT_USERS = [(uid, f"Run scenario {i+1}: evaluate pipeline throughput and errors.") for i, uid in enumerate(ids)]

REQUESTS_PER_USER   = int(os.getenv("TAULAYER_REQS_PER_USER", "2"))   # short + long by default
PRIORITY            = os.getenv("TAULAYER_PRIORITY", "medium")
LONG_REPEAT         = int(os.getenv("TAULAYER_LONG_REPEAT", "40"))    # used to exceed thresholds

# Optional: map provided_user_id -> plaintext API key for those you want to auth via key
# Format: TAULAYER_API_KEYS="apitest_par_01=PLAINTEXT1;apitest_par_08=PLAINTEXT2"
APIKEY_USERS = {}
for pair in os.getenv("TAULAYER_API_KEYS", "").split(";"):
    if "=" in pair:
        uid, key = pair.split("=", 1)
        APIKEY_USERS[uid.strip()] = key.strip()

def make_short(p): return p
def make_long(p):  return " ".join([p] * LONG_REPEAT)

def post_request(provided_user_id, prompt, priority=PRIORITY):
    headers = {}
    if provided_user_id in APIKEY_USERS:
        headers["X-API-Key"] = APIKEY_USERS[provided_user_id]
        # Do not send X-Provided-User-Id if using API key; resolver precedence would pick the header anyway.
    else:
        headers["X-Provided-User-Id"] = provided_user_id
    payload = {"prompt": prompt, "priority": priority}
    return requests.post(POST_URL, json=payload, headers=headers, timeout=TIMEOUT)

def poll_request(rid, max_s=10, every_s=0.5):
    deadline = time.time() + max_s
    last = None
    while time.time() < deadline:
        r = requests.get(GET_URL(rid), timeout=TIMEOUT)
        try:
            data = r.json()
            if data.get("status") in ("completed", "failed", "below_threshold_suggestions_sent"):
                return r, data
            last = (r, data)
        except Exception:
            last = (r, None)
        time.sleep(every_s)
    return last if last else (None, None)

def run():
    # Preflight: ensure users exist (resolver does lookup, not upsert)
    active, missing = [], []
    print("\n==== Preflight: check users exist ====")
    for uid, _ in DEFAULT_USERS:
        try:
            r = post_request(uid, "preflight-only")
            if r.status_code == 200:
                print(f"✅ {uid}: OK")
                active.append((uid, _))
            elif r.status_code == 404:
                print(f"⛔ {uid}: not found")
                missing.append(uid)
            elif r.status_code == 403:
                print(f"⛔ {uid}: invalid API key (403). Check TAULAYER_API_KEYS/hash.")
            else:
                print(f"⚠️ {uid}: status {r.status_code}, body={r.text[:160]}")
        except Exception as e:
            print(f"⚠️ {uid}: exception {e}")

    if missing:
        print("\nCreate these users, then re-run:")
        for uid in missing: print(" -", uid)
        return

    # Build concurrent workload: per user, short + long (or more if REQUESTS_PER_USER > 2)
    work = []
    for uid, base in active:
        for i in range(REQUESTS_PER_USER):
            prompt = make_long(base) if (i % 2 == 1) else make_short(base)
            work.append((uid, prompt))

    total = len(work)
    print(f"\n==== Launching {total} concurrent requests "
          f"({REQUESTS_PER_USER} per user across {len(active)} users; priority={PRIORITY}) ====")

    barrier = threading.Barrier(total)
    lock = threading.Lock()
    results = []
    t0 = time.time()

    def worker(uid, prompt):
        try:
            barrier.wait()
            t_post = time.time()
            resp = post_request(uid, prompt)
            post_ms = (time.time() - t_post) * 1000.0

            rid, final_status, user_id, get_ms = None, None, None, None
            try: rid = resp.json().get("request_id")
            except: pass

            if resp.status_code == 200 and rid:
                t_get = time.time()
                g, data = poll_request(rid)
                get_ms = (time.time() - t_get) * 1000.0
                if data:
                    final_status = data.get("status")
                    user_id = data.get("user_id")

            with lock:
                results.append({
                    "uid": uid,
                    "post_status": resp.status_code if resp else None,
                    "post_ms": post_ms,
                    "rid": rid,
                    "final_status": final_status,
                    "user_id": user_id,
                    "get_ms": get_ms,
                })
        except Exception as e:
            with lock:
                results.append({"uid": uid, "error": str(e)})

    threads = [threading.Thread(target=worker, args=(uid, prompt), daemon=True) for uid, prompt in work]
    for t in threads: t.start()
    for t in threads: t.join()

    wall_ms = (time.time() - t0) * 1000.0
    print(f"\n==== Completed {len(results)} requests in {wall_ms:.1f} ms ====")

    # Per-request summary
    for r in results:
        if "error" in r:
            print(f"[{r['uid']}] ERROR: {r['error']}")
            continue
        print(f"[{r['uid']}] POST {r['post_status']} ({r['post_ms']:.1f} ms) → rid={r['rid']} "
              f"| final={r['final_status']} ({(r['get_ms'] or 0):.1f} ms) | user_id={r['user_id']}")

    # Consistency: each provided_user_id → exactly one user_id
    by_uid = defaultdict(set)
    for r in results:
        if "error" in r: continue
        if r.get("user_id"): by_uid[r["uid"]].add(r["user_id"])

    print("\n==== Consistency check (provided_user_id → user_id) ====")
    ok = True
    for uid, ids in by_uid.items():
        if len(ids) == 1:
            print(f"✅ {uid} → {list(ids)[0]}")
        else:
            print(f"⚠️ {uid} → multiple user_ids observed: {ids}")
            ok = False

    # Final status breakdown
    counts = defaultdict(int)
    for r in results:
        counts[r.get("final_status")] += 1
    print("\n==== Final status breakdown ====")
    for st, c in sorted(counts.items(), key=lambda x: str(x[0])):
        print(f"{st}: {c}")

    if not ok:
        print("\n⚠️ Inconsistencies detected. Investigate identity resolution or DB races.")

if __name__ == "__main__":
    run()
