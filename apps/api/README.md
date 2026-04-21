## Local Setup

Use `uv` to manage the Python version, virtual environment, and dependencies.

```bash
uv python install 3.12
uv venv --python 3.12
uv sync
```

## Local Services

Start PostgreSQL and Redis with Homebrew:

```bash
brew services start postgresql@16
brew services start redis

# If Redis is running correctly, `redis-cli ping` should return `PONG`.
redis-cli ping
```

## Database Migration

Schema changes are now managed by Alembic.

```bash
uv run alembic upgrade head
```

## Run The API

Start the FastAPI development server:

```bash
uv run uvicorn app.main:app --reload
```

Optional health check:

```bash
curl http://127.0.0.1:8000/health
```

## Run The Worker

On macOS, RQ workers may crash because of the platform's `fork()` safety checks.

Before starting the worker, export this environment variable:

```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

Then start the worker:

```bash
uv run rq worker analysis-jobs
```

## Manual API Requests

The REST Client request collection is located at:

```text
http/requests.http
```

## Current Flow

The local MVP flow is currently:

1. Request a presigned upload URL from the API.
2. Upload the video directly to R2.
3. Call `POST /jobs`.
4. The API creates an `analysis_jobs` row and enqueues a background task.
5. The worker downloads the uploaded video, runs `ffprobe`, and updates the job status in Postgres.
6. Successful jobs are marked as `done`; failed jobs are marked as `failed` with an error message.
