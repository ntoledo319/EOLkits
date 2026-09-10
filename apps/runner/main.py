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
RUNNER_MIN_TOKEN_BYTES = 32


def _configured_runner_token() -> bytes | None:
    """Return a production-strength HTTP token, or fail the HTTP surface closed."""
    token = (os.environ.get("RUNNER_TOKEN") or "").encode("utf-8")
    return token if len(token) >= RUNNER_MIN_TOKEN_BYTES else None


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

        token = _configured_runner_token()
        if not token:
            self._write_json(503, {"error": "runner_not_configured"})
            return
        supplied = (self.headers.get("Authorization") or "").encode("latin-1", errors="replace")
        if not hmac.compare_digest(supplied, b"Bearer " + token):
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
            if not isinstance(job, dict) or job.get("type") != "audit_pdf":
                self._write_json(400, {"error": "invalid_job"})
                return
            # Local paths are valid only for the inline/stdin runner. Accepting
            # one from an HTTP caller would let it read any container-readable
            # file. Remote jobs must use the API-generated, signed upload URL.
            if "upload_path" in job:
                self._write_json(400, {"error": "local_input_forbidden"})
                return
            if not job.get("upload_url") and not job.get("uploadUrl"):
                self._write_json(400, {"error": "remote_upload_required"})
                return
            result = run_job(job)
            self._write_json(200, {"success": True, "result": result})
        except (socket.timeout, TimeoutError):
            self._write_json(408, {"error": "request_timeout"})
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self._write_json(400, {"error": "invalid_job"})
        except Exception as exc:
            # Do not reflect provider responses, signed URLs, or local paths to
            # an HTTP client. Operators get only the exception class locally.
            print(f"runner job failed: {type(exc).__name__}", file=sys.stderr)
            self._write_json(500, {"success": False, "error": "job_failed"})
        finally:
            RUNNER_SLOTS.release()

    def log_message(self, format, *args):
        # BaseHTTPRequestHandler's default line contains the full request URI.
        # Signed URLs and caller-supplied query strings must never reach logs.
        return

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
    if not _configured_runner_token():
        raise RuntimeError(
            f"RUNNER_TOKEN must contain at least {RUNNER_MIN_TOKEN_BYTES} UTF-8 bytes"
        )
    port = int(os.environ.get("PORT", "8080"))
    bind = (os.environ.get("RUNNER_BIND") or "127.0.0.1").strip()
    if not bind:
        raise RuntimeError("RUNNER_BIND must not be blank")
    server = ThreadingHTTPServer((bind, port), RunnerHandler)
    server.daemon_threads = True
    print(f"EOLkits runner listening on {bind}:{port}", flush=True)
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
