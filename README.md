# TaskFlow

A distributed task queue , built with Django, DRF, Postgres, and Redis , built to go deep on idempotency, race conditions, and failure recovery.

## How it works

1. Client submits a job (`type`, `payload`, `priority`, optional `idempotency_key` and `max_retries`) via REST API.
2. Job is saved to Postgres and pushed onto a Redis priority queue (sorted set).
3. Workers pull the highest-priority job, claim it with a time-limited lease, run it, and mark it `SUCCESS`, `RETRYING` (with backoff), or `DEAD`.
4. A background "reaper" in every worker recovers jobs whose worker crashed mid-lease.
5. Django admin lets you inspect jobs and bulk-retry dead ones.

```
Client → POST /jobs → Postgres (job record) + Redis (queue)

Worker: ZPOPMIN → claim (conditional update) → run handler → SUCCESS / RETRYING+requeue / DEAD

Reaper (every 10s): expired leases → retry or dead-letter
                    orphaned jobs (missing from Redis) → re-queue
```

**Stack:** Django, DRF, PostgreSQL, Redis, Docker Compose.

## Features

**Idempotency**- DB unique constraint. A check-then-create in Python has a race window; the unique constraint makes Postgres the source of truth. Empty-string keys are normalized to `NULL` before saving, since Postgres treats multiple `NULL`s as non-colliding but multiple `""` as duplicates, this as a real bug, fixed by normalizing rather than relaxing the constraint.

**Priority queue** - Redis sorted set, score = `priority * 10**13 + timestamp`.Priority dominates ordering; timestamp is a FIFO tiebreaker. 

**Visibility timeout + reaper.** Every claim gets a 30s lease. A reaper (every 10s, per worker) reclaims two failure modes: expired leases (worker crashed → retry or dead-letter) and orphaned jobs (in Postgres but missing from Redis → re-queued). No external lock service needed.

**Backoff delay encoded into the queue score.** `ZPOPMIN` has no "not ready yet" concept, so a retry's score uses a future timestamp; a worker popping a not-yet-ready job pushes it back and waits.

**Dead-lettering.** `max_retries` is client-set (bounded 0–10), since different job types tolerate different amounts of failure.

**Manual admin retry resets `attempt_count` to 0**

**Concurrency**


**Lifecycle:** `PENDING → RUNNING → SUCCESS`, or `RUNNING → RETRYING → RUNNING → ... → DEAD` after `max_retries`. Unknown `job_type` goes straight to `DEAD`.

## Running it

**Docker (recommended):**
```bash
docker-compose up --build
docker-compose exec web python manage.py migrate       # first run only
docker-compose exec web python manage.py createsuperuser  # first run only
```
API: `http://localhost:8000/jobs/`
Admin: `http://localhost:8000/admin/`. 
Postgres data persists in a named volume across `down`/`up` (use `down -v` to wipe it).

**Native (for development):**
```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in local DB/Redis values
python manage.py migrate
python manage.py runserver      # terminal 1
python manage.py run_worker     # terminal 2 (run multiple for concurrency)
```

## Tests

```bash
python manage.py test jobs
```

| Test | Proves |
|---|---|
| `JobIdempotencyTests` | Duplicate key → same job returned, no duplicate row. |
| `JobClaimRaceSafetyTests` | Two claims racing for one job → exactly one wins. |
| `JobDeadTests` | Job at `max_retries` → `DEAD`. |
| `JobPriorityTests` | Lower priority number → lower (earlier) score. |
| `JobMaxRetriesTest` | `max_retries` outside 0–10 → rejected. |

## Known limitations

- Single-threaded worker execution (no thread pool per worker yet).
- Backoff delay lives in the same active queue rather than a separate delay structure ,a lone delayed job can cause a tight pop/requeue loop.
