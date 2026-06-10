#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

RESET_VENV=0
START_OPENSEARCH=0
PYTHON_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --reset-venv)
      RESET_VENV=1
      ;;
    --python-only)
      PYTHON_ONLY=1
      ;;
    --start-opensearch)
      START_OPENSEARCH=1
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./setup.sh [options]

Options:
  --reset-venv        Remove and recreate the Python virtual environment
  --python-only       Only prepare the Python virtual environment
  --start-opensearch  Start OpenSearch with docker compose after setup
  -h, --help          Show this help

This script:
  1. Checks required local tools
  2. Creates .env and frontend/.env.local from examples if missing
  3. Creates .venv and installs Python dependencies
  4. Installs frontend dependencies
  5. Generates sample PDFs
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Run ./setup.sh --help for usage." >&2
      exit 1
      ;;
  esac
done

log() {
  printf "\n==> %s\n" "$1"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    echo "Install it first, then rerun ./setup.sh." >&2
    exit 1
  fi
}

log "Checking required tools"
need_cmd python3
need_cmd node
need_cmd npm

python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")
print(f"Python OK: {sys.version.split()[0]}")
PY

node -e "const v=process.versions.node.split('.').map(Number); if (v[0] < 18) { console.error('Node.js 18 or newer is required. Current: ' + process.version); process.exit(1); } console.log('Node OK: ' + process.version);"

log "Preparing local environment files"
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
else
  echo ".env already exists, leaving it unchanged"
fi

if [[ ! -f frontend/.env.local ]]; then
  if [[ -f frontend/.env.local.example ]]; then
    cp frontend/.env.local.example frontend/.env.local
    echo "Created frontend/.env.local from frontend/.env.local.example"
  else
    cat > frontend/.env.local <<'EOF'
# Proxy API requests to the FastAPI backend (same-origin for PDF preview)
BACKEND_URL=http://127.0.0.1:8000

NEXT_PUBLIC_OPENSEARCH_DASHBOARDS_URL=http://localhost:5601
NEXT_PUBLIC_OPENSEARCH_INDEX=docling_demo
EOF
    echo "Created frontend/.env.local with default local settings"
  fi
else
  echo "frontend/.env.local already exists, leaving it unchanged"
fi

log "Setting up Python virtual environment"
if [[ "$RESET_VENV" == "1" ]]; then
  rm -rf .venv
  echo "Removed existing .venv"
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  echo "Created .venv"
else
  echo ".venv already exists"
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

log "Installing frontend dependencies"
if [[ "$PYTHON_ONLY" == "1" ]]; then
  echo "Skipping frontend dependencies (--python-only)"
else
  (cd frontend && npm install)
fi

log "Generating sample documents"
if [[ "$PYTHON_ONLY" == "1" ]]; then
  echo "Skipping sample generation (--python-only)"
else
  .venv/bin/python scripts/generate_nexvalue_samples.py
fi

if [[ "$START_OPENSEARCH" == "1" && "$PYTHON_ONLY" != "1" ]]; then
  log "Starting OpenSearch"
  need_cmd docker
  docker compose up -d
fi

cat <<'EOF'

Setup complete.

Next steps:
  1. Edit .env and set:
       DOCLING_SERVICE_URL=https://your-docling-service-url
       DOCLING_API_KEY=your-api-key

  2. Start OpenSearch:
       npm run opensearch:up

  3. Start the backend:
       npm run backend

  4. Start the frontend in another terminal:
       npm run frontend

  5. Open:
       http://localhost:3000

Optional checks:
  source .env
  curl -H "X-Api-Key: $DOCLING_API_KEY" "$DOCLING_SERVICE_URL/health"
EOF
