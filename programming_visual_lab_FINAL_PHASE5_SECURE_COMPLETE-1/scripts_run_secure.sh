#!/usr/bin/env bash
set -euo pipefail

export PVL_EXECUTION_MODE=docker
export PVL_SANDBOX_IMAGE=programming-visual-lab-sandbox:latest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
