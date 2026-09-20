#!/usr/bin/env bash
set -euo pipefail

docker build -f Dockerfile.sandbox -t programming-visual-lab-sandbox:latest .
echo "Sandbox image built: programming-visual-lab-sandbox:latest"
