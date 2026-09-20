# Phase 5 Security Audit

## Scope

This audit covers the code-execution path added in Phase 5. It does not claim that the application is a hardened public multi-tenant service.

## Security boundary

**Default:** `PVL_EXECUTION_MODE=docker`.

The API host sends a JSON request to a fresh Docker container. Submitted code is not executed in the FastAPI process.

### Container hardening

| Control | Implemented |
|---|---|
| Ephemeral container | Yes (`--rm`) |
| Network disabled | Yes (`--network none`) |
| Read-only root filesystem | Yes (`--read-only`) |
| Writable scratch area | `/tmp` tmpfs only, 64 MiB |
| Non-root | UID/GID 10001 |
| Linux capabilities | `--cap-drop ALL` |
| Privilege escalation | `no-new-privileges` |
| Memory | 256 MiB |
| CPU | 0.50 CPU |
| Process count | 64 PIDs |
| Open files | 64 |
| File size | 3 MiB |
| Host filesystem mounts | None |
| Docker socket mount | None |
| Host execution deadline | Yes |
| Inner execution timeout | Yes |

## Language-level defense in depth

Python:

- imports disabled;
- dangerous builtins disabled;
- dunder names/attributes blocked;
- AST validation before execution;
- tracing/event limit;
- output limit;
- timeout and resource limits inside the runner.

Java:

- package/import statements disabled;
- selected process/filesystem/network/class-loading APIs blocked;
- JVM heap and stack limits;
- compile and run timeouts;
- output/event limits.

These restrictions are **not** the primary security boundary. Docker isolation is.

## Fail-closed behavior

If Docker is not installed/running while secure mode is active, `/api/run` returns `SandboxUnavailable` instead of silently executing user code on the host.

Trusted local development is available only when explicitly selected with:

```text
PVL_EXECUTION_MODE=local
```

## Tested in this environment

Passed:

- Python trace/execution smoke test
- Python recursion event test
- Java compile/run smoke test
- Python blocked-operation tests
- Python timeout test
- Java restricted-API tests
- Java normal-execution regression
- FastAPI `/api/health`
- FastAPI `/api/run` in explicit local mode
- frontend inline JavaScript syntax check
- secure-mode fail-closed behavior when Docker is unavailable

Not executed here:

- Docker image build
- actual container isolation tests

Reason: the current execution environment does not have the Docker CLI/Engine installed. Run `python tests/docker_security.py` on the development machine after Docker Desktop/Engine is running; that suite will build the image and test the real network/filesystem/user/timeout boundary.

## Public deployment recommendations

For public internet exposure, add authentication, rate limiting, concurrency quotas, TLS/reverse proxy, audit logging, monitoring, image scanning/patching, and preferably a separate runner host/VM. Do not mount the Docker socket into an internet-facing application container.
