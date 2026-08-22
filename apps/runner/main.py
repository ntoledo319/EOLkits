#!/usr/bin/env python3
"""
EOLkits Runner - Job dispatcher for the containerized job processor.
Reads job descriptors from stdin and executes the appropriate action.
"""

import hmac
import json
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _positive_int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


RUNNER_SLOTS = threading.BoundedSemaphore(_positive_int_env("RUNNER_CONCURRENCY", 2))
RUNNER_READ_TIMEOUT_SECONDS = _positive_int_env("RUNNER_READ_TIMEOUT_SECONDS", 30)


def run_job(job: dict) -> dict:
    """Dispatch one job descriptor and return a JSON-serializable result."""
    job_type = job.get("type")
    if job_type == "audit_pdf":
        return handle_audit_pdf(job)
    raise ValueError(f"unsupported job type: {job_type}")


def main():
    """Main entry point - reads job from stdin."""
    job = json.load(sys.stdin)
    try:
        result = run_job(job)
        print(json.dumps({"success": True, "result": result}))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e), "error_type": type(e).__name__}))
        sys.exit(1)


class RunnerHandler(BaseHTTPRequestHandler):
    """Small HTTP wrapper for deployed container job runners."""

    def setup(self):
        super().setup()
        self.connection.settimeout(RUNNER_READ_TIMEOUT_SECONDS)

    def do_GET(self):
        if self.path == "/health":
            self._write_json(200, {"ok": True})
            return
        self._write_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path not in ("/", "/job"):
            self._write_json(404, {"error": "not_found"})
            return

        token = os.environ.get("RUNNER_TOKEN")
        if not token:
            self._write_json(503, {"error": "runner_not_configured"})
            return
        supplied = self.headers.get("Authorization") or ""
        if not hmac.compare_digest(supplied, f"Bearer {token}"):
            self._write_json(401, {"error": "unauthorized"})
            return

        if not RUNNER_SLOTS.acquire(blocking=False):
            self._write_json(503, {"error": "runner_capacity_exhausted"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 64 * 1024:
                self._write_json(413, {"error": "invalid_job_size"})
                return
            job = json.loads(self.rfile.read(length) or b"{}")
            result = run_job(job)
            self._write_json(200, {"success": True, "result": result})
        except (socket.timeout, TimeoutError):
            self._write_json(408, {"error": "request_timeout"})
        except Exception as e:
            self._write_json(
                500,
                {"success": False, "error": str(e), "error_type": type(e).__name__},
            )
        finally:
            RUNNER_SLOTS.release()

    def log_message(self, format, *args):
        print(f"runner: {format % args}", file=sys.stderr)

    def _write_json(self, status: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve():
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), RunnerHandler)
    server.daemon_threads = True
    print(f"EOLkits runner listening on :{port}", flush=True)
    server.serve_forever()


def handle_audit_pdf(job: dict) -> dict:
    """Generate an audit PDF report."""
    from audit_pdf import generate_audit_package

    upload_url = job.get("upload_url") or job.get("uploadUrl")
    upload_path = job.get("upload_path")
    email = job.get("email")
    deadline = job.get("deadline")
    filename = job.get("filename")

    package = generate_audit_package(
        upload_url=upload_url,
        upload_path=upload_path,
        email=email,
        deadline=deadline,
        filename=filename,
    )

    return {
        **package,
        "email": email,
    }


if __name__ == "__main__":
    if os.environ.get("RUNNER_HTTP") == "1":
        serve()
    else:
        main()
