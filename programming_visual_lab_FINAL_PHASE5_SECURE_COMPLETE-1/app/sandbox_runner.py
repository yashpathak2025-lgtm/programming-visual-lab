"""Container entrypoint for Programming Visual Lab code execution.
Reads one JSON request from stdin and writes one JSON response to stdout.
The container itself is the security boundary; this process never has network access
when launched by the host execution manager.
"""
import json
import os
import sys

os.environ["PVL_IN_SANDBOX"] = "1"
os.environ["PVL_EXECUTION_MODE"] = "local"

from .executor import execute_local


def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw)
        result = execute_local(
            str(req.get("code", "")),
            str(req.get("language", "python")),
            int(req.get("timeout_ms", 4000)),
        )
    except Exception as exc:
        result = {
            "ok": False,
            "language": "unknown",
            "events": [],
            "stdout": "",
            "error": f"SandboxRunnerError: {type(exc).__name__}: {exc}",
            "source_lines": [],
        }
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
