"""Dashboard updater — single-writer merge for Cloud/Local Dashboard.md.

Cloud writes UPDATE_<source>_<ts>.md files to Updates/.
Local merges those into Dashboard.md and deletes the processed files.

Only Local calls merge — single-writer rule.

Usage:
    from dashboard_updater import DashboardUpdater
    updater = DashboardUpdater()

    # Cloud writes an update signal
    updater.write_update("email_agent", {"emails_processed": 5})

    # Local merges all updates into Dashboard.md
    updater.merge_updates_to_dashboard()
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import UPDATES_DIR, VAULT_PATH, WORK_ZONE
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("dashboard_updater")


class DashboardUpdater:
    """Single-writer Dashboard merge between Cloud and Local zones."""

    def __init__(self) -> None:
        self.updates_dir = UPDATES_DIR
        self.dashboard_path = VAULT_PATH / "Dashboard.md"
        self.updates_dir.mkdir(parents=True, exist_ok=True)

    def write_update(self, source: str, data: dict) -> Path:
        """Write an update signal file to Updates/.

        Called by Cloud agents to signal Dashboard changes.

        Args:
            source: Source identifier (e.g. "email_agent", "cloud_agent").
            data: Key-value data to merge into the Dashboard.

        Returns:
            Path to the created update file.
        """
        timestamp = iso_now().replace(":", "-")
        filename = f"UPDATE_{source}_{timestamp}.md"
        filepath = self.updates_dir / filename

        content = (
            f"# Dashboard Update\n\n"
            f"- **source:** {source}\n"
            f"- **timestamp:** {iso_now()}\n\n"
            f"## Data\n\n"
            f"```json\n{json.dumps(data, indent=2)}\n```\n"
        )
        filepath.write_text(content, encoding="utf-8")

        log_to_vault("dashboard_update_written", source, "success", file=filename)
        logger.info("Dashboard update written: %s", filename)
        return filepath

    def merge_updates_to_dashboard(self) -> int:
        """Merge all Updates/ files into Dashboard.md.

        Only called by Local zone (single-writer rule).

        Returns:
            Number of updates merged.
        """
        if WORK_ZONE != "local":
            logger.debug("Skipping dashboard merge — not in local zone")
            return 0

        if not self.updates_dir.exists():
            return 0

        updates = sorted(
            f for f in self.updates_dir.iterdir()
            if f.is_file() and f.name.startswith("UPDATE_") and not f.name.startswith(".")
        )

        if not updates:
            return 0

        # Read current dashboard
        current = ""
        if self.dashboard_path.exists():
            current = self.dashboard_path.read_text(encoding="utf-8")

        # Build merge section
        merge_lines = [
            "\n## Cloud Updates\n",
            f"> Merged at: {iso_now()}\n",
        ]

        for update_file in updates:
            try:
                content = update_file.read_text(encoding="utf-8")
                # Extract source from filename: UPDATE_<source>_<ts>.md
                parts = update_file.stem.split("_", 2)
                source = parts[1] if len(parts) > 1 else "unknown"

                merge_lines.append(f"\n### {source}\n")
                # Extract the Data section
                if "## Data" in content:
                    data_section = content.split("## Data")[1]
                    merge_lines.append(data_section.strip())

                # Delete processed update
                update_file.unlink()
            except Exception as exc:
                logger.error("Failed to merge %s: %s", update_file.name, exc)

        # Remove old Cloud Updates section if present
        if "## Cloud Updates" in current:
            current = current.split("## Cloud Updates")[0].rstrip()

        # Append new merged section
        merged = current + "\n" + "\n".join(merge_lines) + "\n"
        self.dashboard_path.write_text(merged, encoding="utf-8")

        count = len(updates)
        log_to_vault(
            "dashboard_merge", "dashboard_updater", "success",
            updates_merged=str(count),
        )
        logger.info("Merged %d update(s) into Dashboard.md", count)
        return count
