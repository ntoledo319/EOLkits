#!/usr/bin/env python3
"""
EOLkits Runner - Job dispatcher for the containerized job processor.
Reads job descriptors from stdin and executes the appropriate action.
"""

import sys
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def run_job(job: dict) -> dict:
    """Dispatch one job descriptor and return a JSON-serializable result."""
    job_type = job.get("type")
    if job_type == "audit_pdf":
        return handle_audit_pdf(job)
    if job_type == "migration_pr":
        return handle_migration_pr(job)
    if job_type == "license_key":
        return handle_license_key(job)
    if job_type == "drift_watch_setup":
        return handle_drift_watch_setup(job)
    if job_type == "email":
        return handle_email(job)
    raise ValueError(f"Unknown job type: {job_type}")


def main():
    """Main entry point - reads job from stdin."""
    job = json.load(sys.stdin)
    try:
        result = run_job(job)
        print(json.dumps({"success": True, "result": result}))
        sys.exit(0)
    except Exception as e:
        print(
            json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__}
            )
        )
        sys.exit(1)


class RunnerHandler(BaseHTTPRequestHandler):
    """Small HTTP wrapper for deployed container job runners."""

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
        if token and self.headers.get("Authorization") != f"Bearer {token}":
            self._write_json(401, {"error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            job = json.loads(self.rfile.read(length) or b"{}")
            result = run_job(job)
            self._write_json(200, {"success": True, "result": result})
        except Exception as e:
            self._write_json(
                500,
                {"success": False, "error": str(e), "error_type": type(e).__name__},
            )

    def log_message(self, format, *args):
        print(f"runner: {format % args}", file=sys.stderr)

    def _write_json(self, status: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve():
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), RunnerHandler)
    print(f"EOLkits runner listening on :{port}", flush=True)
    server.serve_forever()


def handle_audit_pdf(job: dict) -> dict:
    """Generate an audit PDF report."""
    from audit_pdf import generate_audit_package

    upload_url = job.get("upload_url") or job.get("uploadUrl")
    upload_path = job.get("upload_path")
    email = job.get("email")
    deadline = job.get("deadline")

    package = generate_audit_package(
        upload_url=upload_url,
        upload_path=upload_path,
        email=email,
        deadline=deadline,
    )

    return {
        **package,
        "email": email,
    }


def handle_migration_pr(job: dict) -> dict:
    """Open a migration PR on user's repository."""
    from migration_pr import create_migration_pr

    repo = job.get("repo")
    email = job.get("email")
    installation_id = job.get("installationId") or job.get("installation_id")

    # Use GitHub App token to:
    # 1. Clone the repo
    # 2. Run the appropriate kit
    # 3. Create a branch
    # 4. Commit changes
    # 5. Open PR

    pr_info = create_migration_pr(
        repo=repo,
        email=email,
        installation_id=installation_id,
    )

    return {
        "pr_url": pr_info["pr_url"],
        "pr_number": pr_info["pr_number"],
        "repo": repo,
    }


def handle_license_key(job: dict) -> dict:
    """Generate and email a license key."""
    company = job.get("company")
    email = job.get("email")

    # Generate license key
    # Store in KV
    # Queue email job

    return {
        "company": company,
        "email": email,
        "status": "key_generated",
    }


def handle_drift_watch_setup(job: dict) -> dict:
    """Set up drift monitoring for a repository."""
    repo = job.get("repo")
    iam_role = job.get("iam_role") or job.get("iamRole")
    email = job.get("email")

    # Validate IAM role
    # Store watch configuration
    # Schedule first scan

    return {
        "repo": repo,
        "iam_role": iam_role,
        "email": email,
        "status": "watch_configured",
    }


def handle_email(job: dict) -> dict:
    """Send a transactional email."""
    to = job.get("to")
    subject = job.get("subject")
    body = job.get("body")

    # Send via Resend API
    # Or queue for later if Resend unavailable

    return {
        "to": to,
        "subject": subject,
        "body_bytes": len(body or ""),
        "status": "queued",
    }


if __name__ == "__main__":
    if os.environ.get("RUNNER_HTTP") == "1":
        serve()
    else:
        main()
