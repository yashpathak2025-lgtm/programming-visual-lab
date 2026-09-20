# Final Audit — Programming Visual Lab Phase 1–5

## Product loop

**CODE → REAL EXECUTION → EVENTS → VISUAL STATE → EXPLANATION → NEXT STEP**

## Included

- Python + Java execution
- real execution events
- current-line highlighting
- variables/state panel
- timeline
- Next / Previous / Auto Play / Restart
- playback speed 0.25×–2×
- beginner explanations
- arrays, loops, IF/ELSE, binary-search range visualization
- Linked List, Stack, Queue, BST, BFS, DFS, recursion and heap visualizations
- Bubble / Selection / Insertion / Merge / Quick / Heap sort lessons
- Python foundations / OOP / exceptions
- Java fundamentals / arrays / OOP / collections
- DSA Question Mode + hints
- quizzes + local progress
- save/export/import
- keyboard shortcuts
- responsive UI + dark/light mode
- Phase 5 Docker execution boundary

## Phase 5 security

Default execution mode is Docker. The host refuses to execute submitted code when Docker is unavailable.

Sandbox flags include:

- `--rm`
- `--network none`
- `--read-only`
- `/tmp` 64 MiB tmpfs
- `--cap-drop ALL`
- `--security-opt no-new-privileges:true`
- `--pids-limit 64`
- `--memory 256m`
- `--memory-swap 256m`
- `--cpus 0.50`
- `--ulimit nofile=64:64`
- `--ulimit fsize=3145728:3145728`
- `--ulimit nproc=64:64`
- `--user 10001:10001`

No host directory or Docker socket is mounted into the sandbox.

## Validation status

### Passed in this build environment

- `python tests/smoke.py`
- `python tests/security.py`
- Python compile checks
- FastAPI health + API run test in explicit local mode
- frontend JavaScript syntax check
- secure-mode fail-closed test

### Requires Docker Desktop/Engine on the target machine

- `python tests/docker_security.py`
- Docker image build
- real container network isolation
- real read-only rootfs check
- real non-root UID check
- real `/tmp` write check
- real container timeout/cleanup check

The audit does not mark those Docker checks as passed until they are actually run on a machine with Docker.
