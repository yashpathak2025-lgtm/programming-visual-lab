# Programming Visual Lab — Final Phase 1–5

A runnable execution-first Programming + DSA learning lab:

**CODE → REAL EXECUTION → EVENTS → VISUAL STATE → EXPLANATION → NEXT STEP**

## What Phase 5 changes

The previous project executed submitted code in the API host process with only language-level restrictions. Phase 5 changes the default to a **fail-closed Docker execution boundary**.

When `PVL_EXECUTION_MODE=docker` (the default):

- the FastAPI host does **not** execute submitted Python/Java code;
- each run starts an ephemeral container;
- network is disabled (`--network none`);
- container root filesystem is read-only;
- only a small `/tmp` tmpfs is writable;
- all Linux capabilities are dropped;
- `no-new-privileges` is enabled;
- the process runs as UID/GID `10001`, not root;
- cgroup limits apply: 256 MiB memory, 0.50 CPU, 64 PIDs;
- file/process descriptor limits are constrained;
- host-side execution deadline is enforced;
- the container is removed after the run;
- no host directory or Docker socket is mounted into the execution container.

This is substantially safer for local/private deployment. A public multi-tenant service should still put the API and runner on isolated infrastructure and add authentication, rate limiting, logging, monitoring, and a dedicated sandbox/VM layer.

## Run securely on Windows + VS Code

**VS Code is the development environment. The website itself opens in your browser. Docker Desktop provides the execution sandbox.**

### 1. Install prerequisites

- VS Code
- Python 3.11+
- Docker Desktop
- JDK 17+ if you also want the local Java toolchain available; the sandbox image contains its own JDK.

Verify:

```powershell
python --version
docker --version
docker info
```

### 2. Open the project in VS Code

Open the extracted `programming_visual_lab_complete` folder.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Build the execution sandbox

```powershell
docker build -f Dockerfile.sandbox -t programming-visual-lab-sandbox:latest .
```

Or run the supplied build script:

```powershell
.\scripts_build_sandbox.bat
```

### 4. Start the secure API

```powershell
$env:PVL_EXECUTION_MODE="docker"
$env:PVL_SANDBOX_IMAGE="programming-visual-lab-sandbox:latest"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or:

```powershell
.\scripts_run_secure.bat
```

Then open:

**http://127.0.0.1:8000**

The browser UI is the learning application; VS Code is where you edit/run the server and tests.

## Trusted local development mode

Docker is intentionally the default. If Docker is not installed, you can still develop the UI/executor locally:

```powershell
$env:PVL_EXECUTION_MODE="local"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

or:

```powershell
.\scripts_run_local.bat
```

**Do not expose local mode to untrusted users or the public internet.**

## Tests

Run the local engine regression suite:

```powershell
$env:PVL_EXECUTION_MODE="local"
python tests/smoke.py
python tests/security.py
```

The secure Docker suite is:

```powershell
python tests/docker_security.py
```

It verifies Docker availability, builds the image, runs isolated Python/Java jobs, checks network denial, checks filesystem isolation, checks timeout behaviour, and confirms the container is removed. If Docker is unavailable, the suite reports exactly which checks could not run rather than pretending they passed.

For a running API, also check:

```text
GET  /api/health
POST /api/run
```

## Architecture

```text
Browser UI
   │
   ▼
FastAPI (/api/run)
   │
   ▼
Execution Manager (host)
   │
   ├── Python request ─┐
   └── Java request ───┤
                       ▼
             Ephemeral Docker container
             network=none
             read-only rootfs
             non-root UID 10001
             cap-drop ALL
             no-new-privileges
             CPU / RAM / PID / file limits
                       │
                       ▼
             Real execution + events
                       │
                       ▼
             JSON execution result
                       │
                       ▼
             Visualizer / timeline / explanation
```

**Important:** Do not mount `/var/run/docker.sock` into the FastAPI application container. Docker socket access is effectively host-root access. For production, use a separate runner service/VM or a controlled container-runtime API.

## Included learning features

- Python + Java execution and real execution events
- current source-line highlighting
- variables/state panel
- stdout/errors
- Run / Pause / Next / Previous / Restart / Auto Play
- 0.25×–2× playback speed
- timeline and beginner explanations
- arrays, loops, IF/ELSE, binary-search ranges
- sorting: Bubble, Selection, Insertion, Merge, Quick, Heap
- Linked List, Stack, Queue, BST, BFS, DFS, recursion, heap views
- Python foundations, OOP and exceptions
- Java fundamentals, arrays, OOP and collections
- DSA Question Mode with starter code and hints
- quizzes, local progress, save/export/import, keyboard shortcuts
- responsive dark/light UI

## Security boundary and limitations

No language-level sandbox should be treated as a complete OS security boundary. The Docker layer is the primary boundary here, while the Python/Java validators are defense-in-depth.

For internet-facing deployment, add:

- authentication/authorization;
- per-user and global rate limits;
- request/concurrency quotas;
- reverse proxy/TLS;
- structured audit logs and alerting;
- dedicated runner hosts/VMs for stronger tenant isolation;
- image signing/scanning and regular patching;
- separate storage from the execution host;
- no Docker socket exposure to untrusted application code.
