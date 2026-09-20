@echo off
setlocal
docker build -f Dockerfile.sandbox -t programming-visual-lab-sandbox:latest .
