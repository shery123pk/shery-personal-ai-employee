"""Task Optimizer Agent — Eisenhower Matrix prioritisation and workload balancing.

Classifies tasks into the four Eisenhower quadrants:
- DO_FIRST: Urgent + Important
- SCHEDULE: Not Urgent + Important
- DELEGATE: Urgent + Not Important
- ELIMINATE: Not Urgent + Not Important
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.base_agent import BaseAgent
from config import NEEDS_ACTION_DIR, PLANS_DIR

_SYSTEM_PROMPT = (
    "You are a productivity expert specialising in the Eisenhower Matrix. "
    "Classify the given task into one of four quadrants: DO_FIRST (urgent+important), "
    "SCHEDULE (important, not urgent), DELEGATE (urgent, not important), or "
    "ELIMINATE (neither). Rate urgency and importance 1-10. Respond as JSON: "
    '{"quadrant": str, "urgency": int, "importance": int, "recommendation": str}'
)


class TaskOptimizer(BaseAgent):
    """Eisenhower Matrix prioritisation and workload balancing."""

    def __init__(self) -> None:
        super().__init__(name="task_optimizer", system_prompt=_SYSTEM_PROMPT)

    def execute(self, task: dict) -> dict:
        """Prioritise all tasks in Needs_Action/.

        Args:
            task: {"scan_folder": bool} or empty dict

        Returns:
            {"prioritized_tasks": list, "matrix_report": str, "report_path": str | None}
        """
        tasks = self._read_pending_tasks()

        if not tasks:
            self.log_action("task_optimization", "skipped", reason="no_pending_tasks")
            return {"prioritized_tasks": [], "matrix_report": "No pending tasks.", "report_path": None}

        classified = []
        for t in tasks:
            classification = self.classify_task(t["description"])
            classification["file"] = t["file"]
            classified.append(classification)

        # Sort: DO_FIRST → SCHEDULE → DELEGATE → ELIMINATE
        priority_order = {"DO_FIRST": 0, "SCHEDULE": 1, "DELEGATE": 2, "ELIMINATE": 3}
        classified.sort(key=lambda x: priority_order.get(x.get("quadrant", "ELIMINATE"), 4))

        report = self.generate_priority_matrix(classified)
        report_path = self._save_report(report)

        self.log_action("task_optimization", "success", task_count=str(len(classified)))

        return {
            "prioritized_tasks": classified,
            "matrix_report": report,
            "report_path": str(report_path) if report_path else None,
        }

    def classify_task(self, task_description: str) -> dict:
        """Classify a single task into an Eisenhower quadrant.

        Returns:
            {"quadrant": str, "urgency": int, "importance": int, "recommendation": str}
        """
        prompt = f"Classify this task:\n\n{task_description}"
        response = self.call_llm(prompt, max_tokens=200)

        # Try JSON parse, fallback to defaults
        import json
        try:
            data = json.loads(response)
            return {
                "quadrant": data.get("quadrant", "SCHEDULE"),
                "urgency": data.get("urgency", 5),
                "importance": data.get("importance", 5),
                "recommendation": data.get("recommendation", "Review and act accordingly"),
            }
        except (json.JSONDecodeError, TypeError):
            return {
                "quadrant": "SCHEDULE",
                "urgency": 5,
                "importance": 5,
                "recommendation": response[:200],
            }

    def generate_priority_matrix(self, tasks: list[dict]) -> str:
        """Create a markdown Eisenhower Matrix report."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        lines = [
            "# Eisenhower Priority Matrix",
            f"\n> Generated: {now}\n",
            "## Summary\n",
            f"Total tasks analysed: {len(tasks)}\n",
        ]

        quadrants = {
            "DO_FIRST": "Do First (Urgent + Important)",
            "SCHEDULE": "Schedule (Important, Not Urgent)",
            "DELEGATE": "Delegate (Urgent, Not Important)",
            "ELIMINATE": "Eliminate (Neither)",
        }

        for key, label in quadrants.items():
            items = [t for t in tasks if t.get("quadrant") == key]
            lines.append(f"\n### {label} ({len(items)})\n")
            if items:
                lines.append("| Task | Urgency | Importance | Recommendation |")
                lines.append("|------|---------|------------|----------------|")
                for item in items:
                    file = item.get("file", "unknown")
                    lines.append(
                        f"| {file} | {item.get('urgency', '-')}/10 "
                        f"| {item.get('importance', '-')}/10 "
                        f"| {item.get('recommendation', '-')[:60]} |"
                    )
            else:
                lines.append("_No tasks in this quadrant._\n")

        return "\n".join(lines)

    def _read_pending_tasks(self) -> list[dict]:
        """Read all tasks from Needs_Action/ folder."""
        tasks = []
        if not NEEDS_ACTION_DIR.exists():
            return tasks
        for item in sorted(NEEDS_ACTION_DIR.iterdir()):
            if item.is_file() and not item.name.startswith("."):
                try:
                    content = item.read_text(encoding="utf-8")
                    tasks.append({"file": item.name, "description": content[:1000]})
                except OSError:
                    continue
        return tasks

    def _save_report(self, report: str) -> Path | None:
        """Save matrix report to Plans/."""
        try:
            PLANS_DIR.mkdir(parents=True, exist_ok=True)
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            path = PLANS_DIR / f"eisenhower_matrix_{date}.md"
            path.write_text(report, encoding="utf-8")
            return path
        except OSError:
            return None
