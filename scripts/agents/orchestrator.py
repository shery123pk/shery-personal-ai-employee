"""Orchestrator Agent — coordinates all agents and manages autonomous task execution.

The central brain of the Gold-tier AI Employee. Routes tasks to the
appropriate specialised agent based on LLM classification.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.base_agent import BaseAgent
from agents.email_agent import EmailAgent
from agents.meeting_agent import MeetingAgent
from agents.research_agent import ResearchAgent
from agents.task_optimizer import TaskOptimizer
from claim_manager import ClaimManager
from config import (
    AUTONOMOUS_MAX_ITERATIONS,
    AUTONOMOUS_RETRY_LIMIT,
    BRIEFINGS_DIR,
    DONE_DIR,
    DOMAINS,
    NEEDS_ACTION_DIR,
    PENDING_APPROVAL_DIR,
    PLANS_DIR,
    WORK_ZONE,
)
from logger import iso_now, log_to_vault, setup_console_logger
from work_zone import WorkZoneRouter

logger = setup_console_logger("orchestrator")

_SYSTEM_PROMPT = (
    "You are the orchestrator for an AI Employee system. Given a task description, "
    "classify it into exactly one category: email, research, meeting, or general. "
    "Respond with a single word."
)


class OrchestratorAgent(BaseAgent):
    """Coordinates all agents, manages autonomous task execution loop."""

    def __init__(self) -> None:
        super().__init__(name="orchestrator", system_prompt=_SYSTEM_PROMPT)
        self.agents: dict[str, BaseAgent] = {
            "email": EmailAgent(),
            "research": ResearchAgent(),
            "meeting": MeetingAgent(),
            "task_optimizer": TaskOptimizer(),
        }
        self.router = WorkZoneRouter(WORK_ZONE)
        self.claimer = ClaimManager("orchestrator")

        # Register CloudAgent when running in cloud zone
        if WORK_ZONE == "cloud":
            from agents.cloud_agent import CloudAgent
            self.agents["cloud"] = CloudAgent()

    def execute(self, task: dict) -> dict:
        """Route a single task to the appropriate agent.

        Args:
            task: {"content": str, "source": str, ...}

        Returns:
            {"agent_used": str, "result": dict}
        """
        content = task.get("content", "")
        task_type = self.classify_task_type(content)

        agent = self.agents.get(task_type)
        if not agent:
            self.log_action("route_task", "fallback", task_type=task_type)
            return {"agent_used": "none", "result": {"summary": "No suitable agent found."}}

        result = agent.execute(task)
        self.log_action("route_task", "success", agent_used=task_type)
        return {"agent_used": task_type, "result": result}

    def classify_task_type(self, content: str) -> str:
        """Classify task content into a type for agent routing.

        Returns: email | research | meeting | general
        """
        # Quick heuristic check before LLM call
        lower = content.lower()
        if any(kw in lower for kw in ("email", "mail", "inbox", "reply", "sender", "from:", "subject:")):
            return "email"
        if any(kw in lower for kw in ("research", "investigate", "analyse", "study", "report on")):
            return "research"
        if any(kw in lower for kw in ("meeting", "agenda", "standup", "sync", "attendee")):
            return "meeting"

        # LLM classification for ambiguous tasks
        response = self.call_llm(
            f"Classify this task: {content[:500]}",
            max_tokens=20,
        ).strip().lower()

        if response in ("email", "research", "meeting"):
            return response
        return "general"

    def run_autonomous_loop(self, max_iterations: int | None = None) -> dict:
        """Autonomous execution loop: scan → prioritise → execute → archive.

        Args:
            max_iterations: Max tasks to process (defaults to config).

        Returns:
            {"processed": int, "errors": int, "results": list}
        """
        max_iters = max_iterations or AUTONOMOUS_MAX_ITERATIONS
        processed = 0
        errors = 0
        results = []

        self.log_action("autonomous_loop_start", "started", max_iterations=str(max_iters))

        # Step 1: Read pending tasks
        pending = self._read_pending_tasks()
        if not pending:
            self.log_action("autonomous_loop", "completed", reason="no_tasks")
            return {"processed": 0, "errors": 0, "results": []}

        # Step 2: Prioritise via TaskOptimizer
        optimizer = self.agents["task_optimizer"]
        optimization = optimizer.execute({})
        prioritized = optimization.get("prioritized_tasks", [])

        # Use prioritized order if available, otherwise process as-is
        task_order = [t["file"] for t in prioritized] if prioritized else [t["file"] for t in pending]

        # Step 3: Process each task with claim-by-move
        for i, filename in enumerate(task_order[:max_iters]):
            filepath = NEEDS_ACTION_DIR / filename
            if not filepath.exists():
                # Also check domain subdirectories
                for domain in DOMAINS:
                    alt = NEEDS_ACTION_DIR / domain / filename
                    if alt.exists():
                        filepath = alt
                        break
                else:
                    continue

            # Claim the file atomically
            claimed = self.claimer.try_claim(filepath)
            if not claimed:
                continue

            # Write current task indicator
            self._write_current_task(filename, i + 1, len(task_order))

            try:
                content = claimed.read_text(encoding="utf-8")
                task_type = self.classify_task_type(content)

                # Check zone routing — delegate if not ours
                zone = self.router.route_task({"domain": task_type})
                if zone != "either" and zone != self.router.zone:
                    self._delegate_to_other_zone(claimed, task_type)
                    processed += 1
                    results.append({"file": filename, "agent": "delegated", "status": "delegated"})
                    continue

                # Execute with retry
                result = self._execute_with_retry(task_type, {
                    "content": content,
                    "source": filename,
                    "subject": filename,
                })

                # Update content and release to Done
                updated = content.replace("**status:** pending", "**status:** completed")
                updated += f"\n- **completed_at:** {iso_now()}\n"
                updated += f"\n- **processed_by:** {task_type}_agent\n"
                claimed.write_text(updated, encoding="utf-8")

                self.claimer.release_to_done(claimed)

                processed += 1
                results.append({"file": filename, "agent": task_type, "status": "success"})

            except Exception as exc:
                errors += 1
                results.append({"file": filename, "status": "error", "detail": str(exc)})
                logger.error("Failed to process %s: %s", filename, exc)
                log_to_vault("autonomous_task_error", filename, "error", detail=str(exc))

        # Cleanup current task indicator
        self._cleanup_current_task()

        self.log_action(
            "autonomous_loop_complete", "success",
            processed=str(processed), errors=str(errors),
        )

        return {"processed": processed, "errors": errors, "results": results}

    def generate_daily_briefing(self) -> Path | None:
        """Generate a morning intelligence summary.

        Returns:
            Path to the generated briefing file.
        """
        BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = BRIEFINGS_DIR / f"gold_briefing_{date}.md"

        # Gather data
        pending_count = self._count_files(NEEDS_ACTION_DIR)
        done_count = self._count_files(DONE_DIR)

        # Ask LLM to format a briefing
        prompt = (
            f"Generate a concise daily briefing for an AI Employee system.\n"
            f"Date: {date}\n"
            f"Pending tasks: {pending_count}\n"
            f"Completed tasks: {done_count}\n"
            f"Include sections: Executive Summary, Task Queue Status, "
            f"Priorities for Today, System Health. Format as markdown."
        )
        content = self.call_llm(prompt, max_tokens=600)

        header = (
            f"# Daily Intelligence Briefing\n\n"
            f"> Date: {date}\n"
            f"> Generated: {iso_now()}\n\n"
            "---\n\n"
        )
        path.write_text(header + content, encoding="utf-8")

        self.log_action("daily_briefing", "success", path=str(path))
        return path

    def generate_weekly_briefing(self) -> Path | None:
        """Generate a CEO strategic audit.

        Returns:
            Path to the generated weekly briefing file.
        """
        BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = BRIEFINGS_DIR / f"weekly_briefing_{date}.md"

        prompt = (
            f"Generate a weekly strategic briefing for a CEO.\n"
            f"Week ending: {date}\n"
            f"Include sections: Week Summary, Key Achievements, "
            f"Pending Items, Strategic Recommendations. "
            f"Format as professional markdown."
        )
        content = self.call_llm(prompt, max_tokens=800)

        header = (
            f"# Weekly Strategic Briefing\n\n"
            f"> Week ending: {date}\n"
            f"> Generated: {iso_now()}\n\n"
            "---\n\n"
        )
        path.write_text(header + content, encoding="utf-8")

        self.log_action("weekly_briefing", "success", path=str(path))
        return path

    def _execute_with_retry(self, task_type: str, task: dict) -> dict:
        """Execute an agent task with retry logic."""
        agent = self.agents.get(task_type)
        if not agent:
            return {"summary": "No handler — task acknowledged"}

        last_error = None
        for attempt in range(AUTONOMOUS_RETRY_LIMIT):
            try:
                return agent.execute(task)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Agent %s attempt %d failed: %s",
                    task_type, attempt + 1, exc,
                )
        raise RuntimeError(f"Agent {task_type} failed after {AUTONOMOUS_RETRY_LIMIT} retries: {last_error}")

    def _read_pending_tasks(self) -> list[dict]:
        """Read all tasks from Needs_Action/ and its domain subdirectories."""
        tasks = []
        if not NEEDS_ACTION_DIR.exists():
            return tasks

        # Scan root
        for item in sorted(NEEDS_ACTION_DIR.iterdir()):
            if item.is_file() and not item.name.startswith("."):
                try:
                    content = item.read_text(encoding="utf-8")
                    tasks.append({"file": item.name, "content": content[:1000]})
                except OSError:
                    continue

        # Scan domain subdirectories
        for domain in DOMAINS:
            domain_dir = NEEDS_ACTION_DIR / domain
            if not domain_dir.exists():
                continue
            for item in sorted(domain_dir.iterdir()):
                if item.is_file() and not item.name.startswith("."):
                    try:
                        content = item.read_text(encoding="utf-8")
                        tasks.append({"file": item.name, "content": content[:1000], "domain": domain})
                    except OSError:
                        continue

        return tasks

    def _delegate_to_other_zone(self, claimed_path: Path, task_type: str) -> None:
        """Delegate a task to the other work zone via Pending_Approval."""
        domain = task_type if task_type in DOMAINS else "general"
        self.claimer.release_to_approval(claimed_path, domain)
        self.log_action("delegate_zone", "delegated", task_type=task_type, domain=domain)

    def _write_current_task(self, filename: str, index: int, total: int) -> None:
        """Write a CURRENT_TASK.md indicator in Plans/."""
        PLANS_DIR.mkdir(parents=True, exist_ok=True)
        path = PLANS_DIR / "CURRENT_TASK.md"
        path.write_text(
            f"# Current Task\n\n"
            f"- **File:** {filename}\n"
            f"- **Progress:** {index}/{total}\n"
            f"- **Started:** {iso_now()}\n",
            encoding="utf-8",
        )

    def _cleanup_current_task(self) -> None:
        """Remove CURRENT_TASK.md indicator."""
        path = PLANS_DIR / "CURRENT_TASK.md"
        if path.exists():
            path.unlink()

    @staticmethod
    def _count_files(directory: Path) -> int:
        """Count non-hidden files in a directory."""
        if not directory.exists():
            return 0
        return len([f for f in directory.iterdir() if f.is_file() and not f.name.startswith(".")])
