"""Health monitor — HTTP health endpoint for Cloud deployment.

Exposes /health returning JSON status of all AI Employee components.

Usage:
    from health_monitor import start_health_server
    start_health_server(port=8080)
"""

import json
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CLOUD_HEALTH_PORT, LOGS_DIR, NEEDS_ACTION_DIR, VAULT_PATH
from logger import setup_console_logger

logger = setup_console_logger("health_monitor")


def _check_vault_accessible() -> dict:
    """Check if the vault directory is accessible."""
    try:
        exists = VAULT_PATH.exists()
        return {"status": "healthy" if exists else "unhealthy", "path": str(VAULT_PATH)}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


def _check_last_log() -> dict:
    """Check the most recent log entry timestamp."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = LOGS_DIR / f"{today}.json"
        if log_file.exists():
            entries = json.loads(log_file.read_text(encoding="utf-8"))
            if entries:
                last = entries[-1].get("timestamp", "unknown")
                return {"status": "healthy", "last_entry": last, "count": len(entries)}
        return {"status": "healthy", "last_entry": "none", "count": 0}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


def _check_pending_tasks() -> dict:
    """Check the Needs_Action queue depth."""
    try:
        count = 0
        if NEEDS_ACTION_DIR.exists():
            count = len([f for f in NEEDS_ACTION_DIR.iterdir() if f.is_file() and not f.name.startswith(".")])
        return {"status": "healthy", "pending_count": count}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


def get_health_status() -> dict:
    """Collect full health status."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "vault": _check_vault_accessible(),
            "logs": _check_last_log(),
            "task_queue": _check_pending_tasks(),
        },
    }


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for /health endpoint."""

    def do_GET(self) -> None:
        if self.path == "/health":
            status = get_health_status()
            body = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default request logging."""


def start_health_server(port: int | None = None) -> HTTPServer:
    """Start the health monitor HTTP server in a daemon thread.

    Args:
        port: Port to listen on (defaults to config).

    Returns:
        The running HTTPServer instance.
    """
    port = port or CLOUD_HEALTH_PORT
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, name="health_http", daemon=True)
    thread.start()
    logger.info("Health monitor listening on port %d", port)
    return server


if __name__ == "__main__":
    server = start_health_server()
    logger.info("Health monitor running. Press Ctrl+C to stop.")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
