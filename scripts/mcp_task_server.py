"""MCP Task Server — FastMCP stdio server with task management tools.

Provides 4 tools for Claude Code to manage tasks via the vault.

Registration:
    claude mcp add task-server -- python scripts/mcp_task_server.py

Usage:
    python scripts/mcp_task_server.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DONE_DIR, NEEDS_ACTION_DIR, PENDING_APPROVAL_DIR
from logger import iso_now, log_to_vault

mcp = FastMCP("task-server")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def create_task(title: str, priority: str = "Medium", due_date: str = "") -> str:
    """Create a new task in Needs_Action/.

    Args:
        title: Task title.
        priority: Priority level (URGENT, REVIEW, FYI, Medium).
        due_date: Optional due date (ISO 8601).

    Returns:
        Confirmation with the created task file path.
    """
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)

    slug = title.lower().replace(" ", "_")[:40]
    filename = f"TASK_{slug}.md"
    path = NEEDS_ACTION_DIR / filename

    content = (
        f"# Task: {title}\n\n"
        f"- **priority:** {priority}\n"
        f"- **status:** pending\n"
        f"- **created_at:** {iso_now()}\n"
        f"- **due_date:** {due_date or 'none'}\n\n"
        f"---\n\n"
        f"Created via MCP task-server.\n"
    )

    path.write_text(content, encoding="utf-8")
    log_to_vault("task_created", "task_server", "success", title=title, priority=priority)

    return (
        f"Task created successfully.\n"
        f"- **Title:** {title}\n"
        f"- **Priority:** {priority}\n"
        f"- **File:** Needs_Action/{filename}\n"
    )


@mcp.tool()
def list_tasks(folder: str = "Needs_Action", status: str = "") -> str:
    """List tasks from a vault folder.

    Args:
        folder: Vault folder to list (Needs_Action, Done, Pending_Approval).
        status: Optional status filter.

    Returns:
        Formatted list of tasks.
    """
    folder_map = {
        "Needs_Action": NEEDS_ACTION_DIR,
        "Done": DONE_DIR,
        "Pending_Approval": PENDING_APPROVAL_DIR,
    }

    target = folder_map.get(folder, NEEDS_ACTION_DIR)
    if not target.exists():
        return f"Folder '{folder}' does not exist."

    files = sorted(f for f in target.iterdir() if f.is_file() and not f.name.startswith("."))

    if not files:
        return f"No tasks in {folder}/."

    lines = [f"Tasks in {folder}/ ({len(files)}):\n"]
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            priority = "unknown"
            for line in content.splitlines():
                if "**priority:**" in line:
                    priority = line.split("**priority:**")[1].strip()
                    break
            lines.append(f"- **{f.name}** [priority: {priority}]")
        except OSError:
            lines.append(f"- **{f.name}** [error reading]")

    return "\n".join(lines)


@mcp.tool()
def update_task(task_filename: str, new_priority: str = "", new_status: str = "") -> str:
    """Update a task's metadata.

    Args:
        task_filename: The task filename in Needs_Action/.
        new_priority: New priority level (leave empty to keep current).
        new_status: New status (leave empty to keep current).

    Returns:
        Confirmation of the update.
    """
    path = NEEDS_ACTION_DIR / task_filename
    if not path.exists():
        return f"Task '{task_filename}' not found in Needs_Action/."

    content = path.read_text(encoding="utf-8")

    if new_priority:
        import re
        content = re.sub(r"\*\*priority:\*\* .+", f"**priority:** {new_priority}", content)
    if new_status:
        import re
        content = re.sub(r"\*\*status:\*\* .+", f"**status:** {new_status}", content)

    content += f"\n- **updated_at:** {iso_now()}\n"
    path.write_text(content, encoding="utf-8")

    log_to_vault("task_updated", "task_server", "success", filename=task_filename)
    return f"Task '{task_filename}' updated successfully."


@mcp.tool()
def optimize_tasks() -> str:
    """Run the TaskOptimizer agent to generate an Eisenhower Matrix.

    Returns:
        Priority matrix report as markdown.
    """
    try:
        from agents.task_optimizer import TaskOptimizer

        optimizer = TaskOptimizer()
        result = optimizer.execute({})
        report = result.get("matrix_report", "No report generated.")
        log_to_vault("task_optimization", "task_server", "success")
        return report
    except Exception as exc:
        return f"Task optimization failed: {exc}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
