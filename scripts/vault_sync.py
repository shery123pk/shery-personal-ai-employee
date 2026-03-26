"""Vault sync — Git-based Cloud/Local vault synchronisation.

Pulls remote changes, commits local changes, and pushes to the shared branch.
Dashboard.md conflicts prefer Local; all other conflicts prefer Cloud ("theirs").

In DEV_MODE: logs actions but skips actual git commands.

Usage:
    from vault_sync import VaultSync
    syncer = VaultSync()
    result = syncer.sync()
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DEV_MODE, VAULT_PATH, VAULT_SYNC_BRANCH
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("vault_sync")


class VaultSync:
    """Git-based vault synchronisation between Cloud and Local zones."""

    def __init__(self, vault_path: Path | None = None, branch: str | None = None) -> None:
        self.vault_path = vault_path or VAULT_PATH
        self.branch = branch or VAULT_SYNC_BRANCH

    def sync(self) -> dict:
        """Full sync cycle: pull → commit local → push.

        Returns:
            {"pulled": int, "pushed": int, "conflicts": list[str]}
        """
        if DEV_MODE:
            logger.info("[DEV_MODE] Vault sync — pull, commit, push (simulated)")
            log_to_vault("vault_sync", "vault_sync", "success", mode="dev")
            return {"pulled": 0, "pushed": 0, "conflicts": []}

        result = {"pulled": 0, "pushed": 0, "conflicts": []}

        # Pull
        pull_result = self.pull()
        result["pulled"] = pull_result.get("pulled", 0)
        result["conflicts"] = pull_result.get("conflicts", [])

        # Resolve any conflicts
        if result["conflicts"]:
            self.resolve_conflicts(result["conflicts"])

        # Commit local changes
        self._run_git(["add", "-A"])
        commit_out = self._run_git(["commit", "-m", f"vault sync {iso_now()}"], allow_fail=True)
        has_commit = commit_out is not None and "nothing to commit" not in commit_out

        # Push
        if has_commit:
            push_result = self.push()
            result["pushed"] = push_result.get("pushed", 0)

        log_to_vault(
            "vault_sync", "vault_sync", "success",
            pulled=str(result["pulled"]),
            pushed=str(result["pushed"]),
            conflicts=str(len(result["conflicts"])),
        )
        return result

    def pull(self) -> dict:
        """Pull remote changes.

        Returns:
            {"pulled": int, "conflicts": list[str]}
        """
        if DEV_MODE:
            logger.info("[DEV_MODE] git pull (simulated)")
            return {"pulled": 0, "conflicts": []}

        output = self._run_git(["pull", "origin", self.branch, "--no-rebase"], allow_fail=True)
        conflicts = []
        pulled = 0

        if output:
            if "CONFLICT" in output:
                for line in output.splitlines():
                    if "CONFLICT" in line:
                        # Extract filename from conflict line
                        parts = line.split()
                        if parts:
                            conflicts.append(parts[-1])
            if "files changed" in output or "file changed" in output:
                pulled = 1

        return {"pulled": pulled, "conflicts": conflicts}

    def push(self) -> dict:
        """Push local commits to remote.

        Returns:
            {"pushed": int}
        """
        if DEV_MODE:
            logger.info("[DEV_MODE] git push (simulated)")
            return {"pushed": 0}

        output = self._run_git(["push", "origin", self.branch], allow_fail=True)
        pushed = 1 if output and "rejected" not in output else 0
        return {"pushed": pushed}

    def resolve_conflicts(self, conflict_files: list[str]) -> None:
        """Resolve merge conflicts.

        Dashboard.md → prefer Local (ours).
        Everything else → prefer Cloud (theirs).
        """
        if DEV_MODE:
            logger.info("[DEV_MODE] Resolving %d conflicts (simulated)", len(conflict_files))
            return

        for filepath in conflict_files:
            if "Dashboard.md" in filepath:
                self._run_git(["checkout", "--ours", filepath])
                logger.info("Conflict resolved (ours/Local): %s", filepath)
            else:
                self._run_git(["checkout", "--theirs", filepath])
                logger.info("Conflict resolved (theirs/Cloud): %s", filepath)
            self._run_git(["add", filepath])

    def _run_git(self, args: list[str], allow_fail: bool = False) -> str | None:
        """Run a git command in the vault directory.

        Args:
            args: Git command arguments (e.g. ["pull", "origin", "main"]).
            allow_fail: If True, return output even on non-zero exit.

        Returns:
            Command stdout, or None on failure.
        """
        cmd = ["git", "-C", str(self.vault_path)] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0 and not allow_fail:
                logger.error("Git command failed: %s\n%s", " ".join(args), result.stderr)
                return None
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            logger.error("Git command timed out: %s", " ".join(args))
            return None
        except FileNotFoundError:
            logger.error("Git not found in PATH")
            return None
