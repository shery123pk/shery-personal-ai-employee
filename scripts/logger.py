"""Centralized logging utility for the AI Employee vault.

Provides console logging and structured JSON logging to the vault's Logs/ folder.
All timestamps use ISO 8601 format.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Vault logs directory
VAULT_LOGS_DIR = Path(__file__).resolve().parent.parent / "AI_Employee_Vault" / "Logs"


def get_today_log_path() -> Path:
    """Return path to today's JSON log file."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return VAULT_LOGS_DIR / f"{today}.json"


def iso_now() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_to_vault(action: str, source: str, result: str, **extra: str) -> None:
    """Append a structured JSON entry to today's vault log file.

    Args:
        action: What happened (e.g. "file_detected", "processed").
        source: The file or entity involved.
        result: Outcome (e.g. "success", "error").
        **extra: Additional key-value pairs to include.
    """
    log_path = get_today_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing entries
    entries: list[dict] = []
    if log_path.exists():
        try:
            entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []

    entry = {
        "timestamp": iso_now(),
        "action": action,
        "source": source,
        "result": result,
        **extra,
    }
    entries.append(entry)

    log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def setup_console_logger(name: str = "ai_employee") -> logging.Logger:
    """Configure and return a console logger with ISO 8601 timestamps."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
