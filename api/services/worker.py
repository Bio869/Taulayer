# api/services/worker.py
import asyncio
import os
from services.scheduler import (
    lease_jobs,
    complete_job,
    fail_and_reschedule,
    release_stale_locks,
)
from services.executor import execute_request_job
from services.logger import log

WORKER_ID = os.getenv("HOSTNAME", "worker-1")
SLEEP_IDLE_SEC = 0.5  # time to wait if no jobs found


async def start_worker_loop():
    """
    Continuously lease and execute jobs from the jobs table.
    Intended to run in its own process or as a background task.
    """
    log.info("Worker loop starting", extra={"worker_id": WORKER_ID})

    while True:
        try:
            jobs = await lease_jobs(worker_id=WORKER_ID, limit=10)

            if not jobs:
                # No jobs ready — release any stale locks just in case
                await release_stale_locks()
                await asyncio.sleep(SLEEP_IDLE_SEC)
                continue

            for job in jobs:
                job_id = job["id"]
                request_id = job["request_id"]

                try:
                    # This runs your actual business logic for the request
                    await execute_request_job(request_id)
                    await complete_job(job_id)
                    log.info("Job completed", extra={"job_id": job_id, "request_id": request_id})

                except Exception as e:
                    await fail_and_reschedule(job_id, str(e))
                    log.error("Job failed", extra={"job_id": job_id, "request_id": request_id, "error": str(e)})

        except Exception as outer:
            log.exception("Worker loop error", extra={"error": str(outer)})
            await asyncio.sleep(1.0)
