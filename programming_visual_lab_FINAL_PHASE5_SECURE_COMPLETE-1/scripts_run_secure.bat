@echo off
set PVL_EXECUTION_MODE=docker
set PVL_SANDBOX_IMAGE=programming-visual-lab-sandbox:latest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
