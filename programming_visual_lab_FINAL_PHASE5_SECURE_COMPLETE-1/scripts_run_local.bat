@echo off
rem TRUSTED DEVELOPMENT ONLY - do not expose this mode publicly.
set PVL_EXECUTION_MODE=local
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
