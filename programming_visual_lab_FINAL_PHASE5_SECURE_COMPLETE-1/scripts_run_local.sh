#!/usr/bin/env bash
set -euo pipefail

# Trusted-development mode only. Never expose this mode to untrusted users.
export PVL_EXECUTION_MODE=local
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
