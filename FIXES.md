# FIXES.md

## Fix 1
- **File:** `api/main.py`
- **Line:** 8
- **Problem:** Redis host hardcoded as `localhost`. In a Docker network, services communicate via service name, not localhost.
- **Fix:** Changed `host="localhost"` to `host=redis`

## Fix 2
- **File:** `api/main.py`
- **Line:** 14
- **Problem:** Endpoint path `/jobs/{job_id}a` has a stray `a` making the route unreachable.
- **Fix:** Changed to `/jobs/{job_id}`

## Fix 3
- **File:** `worker/worker.py`
- **Line:** 6
- **Problem:** Redis host hardcoded as `localhost`. In a Docker network, services communicate via service name, not localhost.
- **Fix:** Changed to `host=os.getenv("REDIS_HOST", "redis")`

## Fix 4
- **File:** `api/main.py` and `worker/worker.py`
- **Line:** 8 (api), 6 (worker)
- **Problem:** Redis password defined in `.env` as `REDIS_PASSWORD` was never passed to the Redis client, causing authentication failure when Redis requires a password.
- **Fix:** Added `password=os.getenv("REDIS_PASSWORD")` to both Redis connections

## Fix 5
- **File:** `frontend/app.js`
- **Line:** 6
- **Problem:** API URL hardcoded as `http://localhost:8000`. In a Docker network, the frontend container cannot reach the API via localhost.
- **Fix:** Changed to `http://${process.env.API_HOST || 'api'}:8000`

## Fix 6
- **File:** `frontend/views/index.html`
- **Line:** 35
- **Problem:** `pollJob()` checks `data.status !== 'completed'` without guarding against undefined. If the API returns an error (e.g. job not found), `data.status` is undefined and the poll loop runs forever.
- **Fix:** Added `data.status &&` guard before the comparison

## Fix 8
- **File:** `frontend/views/index.html`
- **Line:** 23, 31
- **Problem:** `submitJob()` and `pollJob()` had no try/catch blocks. A network failure or bad response would crash silently — the user would see no feedback and job status would freeze.
- **Fix:** Wrapped both functions in try/catch with user-visible error messages

## Fix 7
- **File:** `api/requirements.txt`, `worker/requirements.txt`, `api/main.py`, `worker/worker.py`
- **Problem:** `python-dotenv` was missing from both requirements files. Without it, `os.getenv()` cannot load values from the `.env` file, so `REDIS_PASSWORD` would always be `None` when running locally.
- **Fix:** Added `python-dotenv` to both requirements files and added `load_dotenv()` call at the top of both Python files

## Fix 9
- **File:** `worker/` (missing `.env`)
- **Problem:** The worker directory had no `.env` file. `load_dotenv()` searches the current working directory, so running the worker from its own folder meant `REDIS_PASSWORD` was never loaded, causing `AuthenticationError: Authentication required` at runtime.
- **Fix:** Created `worker/.env` with `REDIS_HOST`, `REDIS_PASSWORD`, and `APP_ENV` matching `api/.env`

## Fix 10
- **File:** `api/.env`
- **Problem:** `REDIS_HOST` was not defined in `.env`, so `os.getenv("REDIS_HOST", "redis")` always defaulted to `"redis"` locally (a hostname that only exists inside Docker). The API connected fine only because `REDIS_HOST=localhost` was passed manually on the command line — not from the env file.
- **Fix:** Added `REDIS_HOST=localhost` to `api/.env`

## Fix 11
- **File:** `frontend/app.js`, `frontend/package.json`, `frontend/` (missing `.env`)
- **Problem:** `app.js` used `process.env.API_HOST` but had no dotenv setup and no `.env` file. `API_HOST` was always `undefined` locally, so the app defaulted to `http://api:8000` — a hostname that only resolves inside Docker. Every `/submit` and `/status` call returned 500.
- **Fix:** Added `require('dotenv').config()` to `app.js`, installed `dotenv` package, and created `frontend/.env` with `API_HOST=localhost` so local runs load it automatically without manual overrides