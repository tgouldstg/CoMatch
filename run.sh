#!/usr/bin/env bash
set -euo pipefail

# Portable runner: uses local Python if available, otherwise Docker.
if python3 -m pip --version >/dev/null 2>&1; then
  python3 -m pip install -r requirements.txt
  exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
  echo "python3-pip not available; running via Docker..."
  docker build -t company-match-api:local .
  exec docker run --rm -p 8000:8000 company-match-api:local
fi
