#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

RESET_VENV=0
START_OPENSEARCH=0
OPENSEARCH_ONLY=0
STOP_OPENSEARCH=0
PYTHON_ONLY=0
COMPOSE_CMD=()

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
    --opensearch-only)
      OPENSEARCH_ONLY=1
      START_OPENSEARCH=1
      ;;
    --stop-opensearch)
      STOP_OPENSEARCH=1
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./setup.sh [options]

Options:
  --reset-venv        Remove and recreate the Python virtual environment
  --python-only       Only prepare the Python virtual environment
  --start-opensearch  Start OpenSearch with a Compose-compatible runtime after setup
  --opensearch-only   Only start OpenSearch, then exit
  --stop-opensearch   Stop OpenSearch, then exit
  -h, --help          Show this help

This script:
  1. Checks required local tools
  2. Installs Node.js with Homebrew if Node/npm are missing on macOS
  3. Creates .env and frontend/.env.local from examples if missing
  4. Creates .venv and installs Python dependencies
  5. Installs frontend dependencies
  6. Generates sample PDFs
  7. Optionally starts OpenSearch with Docker, Rancher Desktop, Podman, or Colima
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

install_node_with_brew() {
  if command -v brew >/dev/null 2>&1; then
    echo "Node.js/npm not found. Installing Node.js with Homebrew..."
    brew install node
    return
  fi

  cat >&2 <<'EOF'
Missing Node.js/npm.

Install Node.js 18 or newer, then rerun ./setup.sh.

macOS with Homebrew:
  brew install node

macOS without Homebrew:
  Install Node.js LTS from https://nodejs.org/

Ubuntu/Debian example:
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
EOF
  exit 1
}

ensure_node() {
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    install_node_with_brew
  fi

  if ! node -e "const v=process.versions.node.split('.').map(Number); process.exit(v[0] >= 18 ? 0 : 1);"; then
    echo "Node.js 18 or newer is required. Current: $(node --version)" >&2
    if command -v brew >/dev/null 2>&1; then
      echo "Upgrading Node.js with Homebrew..."
      brew upgrade node || brew install node
    else
      echo "Please install Node.js 18 or newer from https://nodejs.org/ and rerun ./setup.sh." >&2
      exit 1
    fi
  fi
}

detect_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    return
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
    return
  fi

  if command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(podman compose)
    return
  fi

  if command -v podman-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(podman-compose)
    return
  fi

  cat >&2 <<'EOF'
Could not find a Docker Compose compatible runtime.

Install one of these, then rerun the command:
  - Docker Desktop: https://www.docker.com/products/docker-desktop/
  - Rancher Desktop: https://rancherdesktop.io/ (enable dockerd / Docker-compatible mode)
  - Podman Desktop: https://podman-desktop.io/ plus podman-compose if needed

After installing, verify one of these works:
  docker compose version
  docker-compose version
  podman compose version
  podman-compose --version
EOF
  exit 1
}

compose_up() {
  detect_compose
  echo "Using container runtime: ${COMPOSE_CMD[*]}"
  "${COMPOSE_CMD[@]}" up -d
}

compose_down() {
  detect_compose
  echo "Using container runtime: ${COMPOSE_CMD[*]}"
  "${COMPOSE_CMD[@]}" down
}

if [[ "$STOP_OPENSEARCH" == "1" ]]; then
  log "Stopping OpenSearch"
  compose_down
  exit 0
fi

if [[ "$OPENSEARCH_ONLY" == "1" ]]; then
  log "Starting OpenSearch"
  compose_up
  exit 0
fi

log "Checking required tools"
need_cmd python3
ensure_node

python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")
print(f"Python OK: {sys.version.split()[0]}")
PY

node -e "console.log('Node OK: ' + process.version);"
npm --version >/dev/null

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
  compose_up
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
