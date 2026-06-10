#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
exec .venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
