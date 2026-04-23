# hng14-stage2-devops

A containerized three-service job-queue application. A FastAPI HTTP API accepts job submissions, a Python worker processes them asynchronously, and an Express frontend exposes a simple submit/status interface. Redis serves as the message broker and job state store.

## Architecture

| Service  | Language          | Role                                                                 |
|----------|-------------------|----------------------------------------------------------------------|
| redis    | Redis 7 (Alpine)  | Message broker and job state store. Not exposed to host.             |
| api      | Python / FastAPI  | HTTP API. Accepts `POST /jobs`, returns status via `GET /jobs/{id}`. |
| worker   | Python            | Consumes jobs from Redis, processes them, writes status back.        |
| frontend | Node / Express    | Web-facing service on host port 3000. Proxies to the API.            |

All internal communication runs on a private Docker network. Only the frontend is reachable from the host.

## Prerequisites

You need the following installed on a clean machine before starting:

| Tool            | Minimum version | Verify with             |
|-----------------|-----------------|-------------------------|
| Docker Engine   | 24.0            | `docker --version`      |
| Docker Compose  | v2.20           | `docker compose version`|
| Git             | 2.30            | `git --version`         |

No language runtimes (Python, Node) are needed on the host — everything runs inside containers.

## Bringing the stack up

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/hng14-stage2-devops.git
cd hng14-stage2-devops
```

### 2. Create the environment file

Copy the example file and fill in real values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
REDIS_PASSWORD=change-me-to-a-strong-secret
APP_ENV=production
FRONTEND_PORT=3000
```

All three variables are required. `REDIS_PASSWORD` must be non-empty — Redis will fail to start otherwise.

### 3. Build and start the stack

```bash
docker compose up --build -d
```

This will:
- Build three images (`api`, `worker`, `frontend`) from their respective Dockerfiles
- Pull the `redis:7-alpine` image
- Create two Docker networks (`internal`, `frontend`)
- Start all four services in dependency order (`redis` → `api` + `worker` → `frontend`)

The first run takes 2-3 minutes while images are built and layers are cached. Subsequent runs start in seconds.

### 4. Verify everything is healthy

```bash
docker compose ps
```

A successful startup looks like this:

```
NAME                              IMAGE                           STATUS                   PORTS
hng14-stage2-devops-api-1         hng14-stage2-devops-api         Up 30 seconds (healthy)
hng14-stage2-devops-frontend-1    hng14-stage2-devops-frontend    Up 20 seconds (healthy)  0.0.0.0:3000->3000/tcp
hng14-stage2-devops-redis-1       redis:7-alpine                  Up 45 seconds (healthy)
hng14-stage2-devops-worker-1      hng14-stage2-devops-worker      Up 30 seconds (healthy)
```

Every container must show `(healthy)` in the `STATUS` column. If any show `(unhealthy)` or `(starting)` after 60 seconds, see [Troubleshooting](#troubleshooting).

## Verifying the stack works end-to-end

### Submit a job through the frontend

```bash
curl -X POST http://localhost:3000/submit
```

Expected response (the UUID will differ):

```json
{"job_id":"3f4a1c88-9e2b-4d3a-8c71-7f2b5d6a9c01"}
```

### Check the job status

Using the `job_id` returned above:

```bash
curl http://localhost:3000/status/3f4a1c88-9e2b-4d3a-8c71-7f2b5d6a9c01
```

Immediately after submission you should see:

```json
{"job_id":"3f4a1c88-9e2b-4d3a-8c71-7f2b5d6a9c01","status":"queued"}
```

After roughly 2 seconds (worker processing time):

```json
{"job_id":"3f4a1c88-9e2b-4d3a-8c71-7f2b5d6a9c01","status":"completed"}
```

A transition from `queued` to `completed` confirms all four services are communicating correctly: frontend → api → redis → worker → redis → api → frontend.

## Service endpoints

| Endpoint                         | Method | Purpose                             |
|----------------------------------|--------|-------------------------------------|
| `http://localhost:3000/`         | GET    | Web UI (static page)                |
| `http://localhost:3000/submit`   | POST   | Submit a new job                    |
| `http://localhost:3000/status/:id` | GET  | Query job status                    |

The API runs inside the internal network at `api:8000` and is not reachable from the host. Redis is not reachable from the host at all.

## Stopping the stack

Graceful shutdown (preserves volumes):

```bash
docker compose down
```

Full teardown (removes volumes and networks):

```bash
docker compose down -v --remove-orphans
```

## Troubleshooting

### Redis container exits immediately

Check that `REDIS_PASSWORD` is set and non-empty in `.env`. Redis will fail to start with an empty `--requirepass` value.

```bash
docker compose logs redis
```

### Worker container stays unhealthy

Check whether Redis is actually reachable from the worker:

```bash
docker compose logs worker
```

The worker healthcheck only verifies the process is running; if the worker cannot reach Redis it will still show healthy but will silently fail to process jobs. Confirm Redis is healthy first.

### Port 3000 already in use

Override the host port via `.env`:

```env
FRONTEND_PORT=3001
```

Then submit jobs against `http://localhost:3001/submit`.

### Rebuild from scratch

If images get into an inconsistent state:

```bash
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up -d
```

## Running tests

Unit tests (requires Python 3.12 on the host):

```bash
cd api
pip install -r requirements.txt pytest pytest-cov httpx
pytest tests/ -v --cov=.
```

CI runs the full test and integration suite on every push. See `.github/workflows/pipeline.yml`.
