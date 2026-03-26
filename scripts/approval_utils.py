"""Approval workflow utilities — Human-in-the-Loop.

Creates approval request files in Pending_Approval/ for sensitive actions.
Humans review and move files to Approved/ or Rejected/ to signal decisions.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import PENDING_APPROVAL_DIR
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("approval")


def create_approval_request(
    action_type: str,
    summary: str,
    details: dict | None = None,
    domain: str = "",
) -> Path:
    """Create an approval request file in Pending_Approval/.

    Args:
        action_type: Type of action (e.g. "send_email", "post_linkedin").
        summary: Human-readable one-line summary.
        details: Additional metadata to include.
        domain: Optional domain subdirectory (e.g. "email", "social").

    Returns:
        Path to the created approval file.
    """
    if domain:
        target_dir = PENDING_APPROVAL_DIR / domain
    else:
        target_dir = PENDING_APPROVAL_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = iso_now()
    slug = action_type.replace(" ", "_").lower()
    filename = f"APPROVE_{slug}_{timestamp.replace(':', '-')}.md"
    filepath = target_dir / filename

    details = details or {}
    details_block = "\n".join(f"- **{k}:** {v}" for k, v in details.items())

    content = (
        f"# Approval Request: {summary}\n"
        f"\n"
        f"- **action_type:** {action_type}\n"
        f"- **requested_at:** {timestamp}\n"
        f"- **status:** pending_approval\n"
        f"\n"
        f"## Details\n"
        f"\n"
        f"{details_block}\n"
        f"\n"
        f"## Action Data\n"
        f"\n"
        f"```json\n"
        f"{json.dumps(details, indent=2, ensure_ascii=False)}\n"
        f"```\n"
        f"\n"
        f"---\n"
        f"\n"
        f"**Instructions:** Review this request and move this file to:\n"
        f"- `Approved/` — to execute the action\n"
        f"- `Rejected/` — to deny the action\n"
    )

    filepath.write_text(content, encoding="utf-8")

    log_to_vault(
        action="approval_requested",
        source=action_type,
        result="pending",
        summary=summary,
        file=filename,
    )
    logger.info("Approval request created: %s → %s", action_type, filename)

    return filepath
