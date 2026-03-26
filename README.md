# Company Match API (FastAPI)

A starter API for matching company names across two input streams.

## Features
- Login-required API via JWT bearer token (`/auth/login`, `/auth/me`)
- `/match` endpoint with confidence scoring (auth required)
- `/match/csv` endpoint for two-file CSV uploads (auth required)
- Name normalization (case/punctuation/legal suffix removal)
- Fuzzy similarity scoring
- Optional website and country boost
- Decision bands: `auto_accept`, `review`, `reject`

## Quick start

### Option A: one command (auto-detect)

```bash
cd company-match-api
export APP_AUTH_USERNAME='your-admin-user'
export APP_AUTH_PASSWORD='choose-a-strong-password'
export APP_AUTH_SECRET='long-random-secret-at-least-32-chars'
./run.sh
```

`run.sh` uses local Python/pip when available, otherwise falls back to Docker.

### Option B: local Python

```bash
cd company-match-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Option C: Docker

```bash
cd company-match-api
docker build -t company-match-api:local .
docker run --rm -p 8000:8000 company-match-api:local
```

Web UI: http://localhost:8000/
Open docs: http://localhost:8000/docs

UI features:
- Built-in login form
- JSON input mode
- CSV upload mode
- Match table view
- Decision/confidence/text filters (including review queue view)
- Download visible rows as CSV
- Download full result as JSON

## Authentication

Endpoints:
- `POST /auth/login` (public)
- `GET /auth/me` (requires bearer token)
- `POST /match` (requires bearer token)
- `POST /match/csv` (requires bearer token)

Environment variables:
- `APP_AUTH_USERNAME` (default: `admin`, change this)
- `APP_AUTH_PASSWORD` (default: `change-me-now`, change this)
- `APP_AUTH_SECRET` (JWT signing secret; set a long random value)
- `APP_AUTH_TOKEN_TTL_HOURS` (default: `24`)

## Example request (JSON)

```bash
curl -s http://localhost:8000/match \
  -H 'content-type: application/json' \
  -d '{
    "left": [
      {"id": "l1", "name": "Acme Holdings LLC", "website": "acme.com", "country": "US"}
    ],
    "right": [
      {"id": "r1", "name": "ACME Holding Co.", "website": "acme.com", "country": "US"},
      {"id": "r2", "name": "Globex International Ltd", "website": "globex.com", "country": "US"}
    ],
    "options": {
      "top_k": 3,
      "auto_accept_threshold": 0.92,
      "review_threshold": 0.75
    }
  }' | jq
```

## Example request (CSV upload)

Both files must include headers with at least: `id,name`.
Optional columns: `website,country`. Extra columns are preserved in metadata.

```bash
curl -s http://localhost:8000/match/csv \
  -F "left_file=@left.csv" \
  -F "right_file=@right.csv" \
  -F "top_k=3" \
  -F "auto_accept_threshold=0.92" \
  -F "review_threshold=0.75" | jq
```

## Response shape
- `results[]`
  - `left_id`, `left_name`
  - `best_match` (`id`, `name`, `confidence`, `score_breakdown`)
  - `alternatives[]`
  - `decision`
- `summary`
  - counts for `auto_accept`, `review`, `reject`

## Internet deployment
See `DEPLOY.md` for recommended internet exposure using Cloudflare Tunnel + Docker.

## Notes
This is a production-ready scaffold, not a fully tuned model. Next upgrades:
- better blocking/candidate generation for large datasets
- learned calibration using labeled pairs
- async job endpoint for huge batches
- persistence and audit logs
- rate limiting and account management
