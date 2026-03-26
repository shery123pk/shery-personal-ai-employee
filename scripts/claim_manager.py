"""Claim-by-move concurrency manager for the AI Employee.

Provides atomic file claiming via os.rename() to prevent multiple agents
from processing the same task simultaneously.

Usage:
    claimer = ClaimManager("email_agent")
    claimed = claimer.try_claim(needs_action_path)
    if claimed:
        # process the file ...
        claimer.release_to_done(claimed)
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DONE_DIR, IN_PROGRESS_DIR, NEEDS_ACTION_DIR, PENDING_APPROVAL_DIR
from logger import log_to_vault, setup_console_logger

logger = setup_console_logger("claim_manager")


class ClaimManager:
    """Atomic claim-by-move for concurrent agent task processing."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self.claim_dir = IN_PROGRESS_DIR / agent_name
        self.claim_dir.mkdir(parents=True, exist_ok=True)

    def try_claim(self, source_path: Path) -> Path | None:
        """Atomically claim a file by moving it to In_Progress/<agent>/.

        Args:
            source_path: Path to file in Needs_Action/ (or subdirectory).

        Returns:
            Path to the claimed file in In_Progress/<agent>/, or None if claim failed.
        """
        if not source_path.exists():
            return None

        dest = self.claim_dir / source_path.name
        try:
            os.rename(str(source_path), str(dest))
            log_to_vault(
                action="task_claimed",
                source=source_path.name,
                result="success",
                agent=self.agent_name,
            )
            logger.info("Claimed: %s → In_Progress/%s/", source_path.name, self.agent_name)
            return dest
        except OSError:
            # Another agent already moved/claimed this file
            logger.debug("Claim failed (already taken): %s", source_path.name)
            return None

    def release_to_done(self, claimed_path: Path) -> Path | None:
        """Move a claimed file to Done/.

        Args:
            claimed_path: Path inside In_Progress/<agent>/.

        Returns:
            Path in Done/, or None on failure.
        """
        if not claimed_path.exists():
            return None

        DONE_DIR.mkdir(parents=True, exist_ok=True)
        dest = DONE_DIR / claimed_path.name
        try:
            os.rename(str(claimed_path), str(dest))
            log_to_vault(
                action="task_released_done",
                source=claimed_path.name,
                result="success",
                agent=self.agent_name,
            )
            logger.info("Released to Done: %s", claimed_path.name)
            return dest
        except OSError as exc:
            logger.error("Failed to release %s to Done: %s", claimed_path.name, exc)
            return None

    def release_to_approval(self, claimed_path: Path, domain: str = "") -> Path | None:
        """Move a claimed file to Pending_Approval/ (optionally in a domain subdir).

        Args:
            claimed_path: Path inside In_Progress/<agent>/.
            domain: Optional domain subdirectory (e.g. "email", "social").

        Returns:
            Path in Pending_Approval/, or None on failure.
        """
        if not claimed_path.exists():
            return None

        if domain:
            dest_dir = PENDING_APPROVAL_DIR / domain
        else:
            dest_dir = PENDING_APPROVAL_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest = dest_dir / claimed_path.name
        try:
            os.rename(str(claimed_path), str(dest))
            log_to_vault(
                action="task_released_approval",
                source=claimed_path.name,
                result="success",
                agent=self.agent_name,
                domain=domain,
            )
            logger.info("Released to Pending_Approval/%s: %s", domain, claimed_path.name)
            return dest
        except OSError as exc:
            logger.error("Failed to release %s to approval: %s", claimed_path.name, exc)
            return None

    def cleanup_stale(self, max_age_seconds: int = 3600) -> list[Path]:
        """Return stale claims (older than max_age_seconds) back to Needs_Action/.

        Args:
            max_age_seconds: Maximum age in seconds before a claim is considered stale.

        Returns:
            List of paths that were returned to Needs_Action/.
        """
        returned = []
        now = time.time()

        if not self.claim_dir.exists():
            return returned

        for item in self.claim_dir.iterdir():
            if item.is_file() and not item.name.startswith("."):
                try:
                    age = now - item.stat().st_mtime
                    if age > max_age_seconds:
                        dest = NEEDS_ACTION_DIR / item.name
                        os.rename(str(item), str(dest))
                        returned.append(dest)
                        log_to_vault(
                            action="stale_claim_returned",
                            source=item.name,
                            result="success",
                            agent=self.agent_name,
                            age_seconds=str(int(age)),
                        )
                        logger.warning("Stale claim returned: %s (age: %ds)", item.name, int(age))
                except OSError:
                    continue

        return returned
