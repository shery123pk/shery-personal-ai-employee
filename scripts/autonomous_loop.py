"""Autonomous execution loop (Ralph Wiggum system).

Scans Needs_Action/, prioritises via TaskOptimizer, routes to
appropriate agents, executes with retry, and archives to Done/.

Usage:
    python scripts/autonomous_loop.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import AUTONOMOUS_MAX_ITERATIONS, AUTONOMOUS_RETRY_LIMIT
from logger import log_to_vault, setup_console_logger

logger = setup_console_logger("autonomous_loop")


class RetryHandler:
    """Exponential backoff retry logic for agent execution."""

    def __init__(self, max_retries: int | None = None) -> None:
        self.max_retries = max_retries or AUTONOMOUS_RETRY_LIMIT

    def execute_with_retry(self, func, *args, **kwargs) -> dict:
        """Execute a function with retry on transient failures.

        Returns:
            The function result or a dict with error info.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                wait = 2 ** attempt
                logger.warning(
                    "Attempt %d/%d failed: %s — retrying in %ds",
                    attempt + 1, self.max_retries, exc, wait,
                )
                time.sleep(wait)

        logger.error("All %d retries exhausted: %s", self.max_retries, last_error)
        return {"status": "error", "detail": str(last_error)}


def run_autonomous_loop(max_iterations: int | None = None) -> dict:
    """Main autonomous execution loop.

    1. Scan Needs_Action/ for pending tasks
    2. Run TaskOptimizer to prioritise
    3. For each task (up to MAX_ITERATIONS):
       a. Classify task type via LLM
       b. Route to appropriate agent
       c. Execute with retry (up to RETRY_LIMIT)
       d. On success: archive to Done/
       e. On failure: log error, skip, continue
    4. Generate execution report in Plans/

    Args:
        max_iterations: Override for max tasks to process.

    Returns:
        {"processed": int, "errors": int, "results": list}
    """
    from agents.orchestrator import OrchestratorAgent

    orchestrator = OrchestratorAgent()

    logger.info("Starting autonomous loop (max_iterations=%s)", max_iterations or AUTONOMOUS_MAX_ITERATIONS)
    log_to_vault("autonomous_loop_started", "autonomous_loop", "started")

    result = orchestrator.run_autonomous_loop(max_iterations)

    logger.info(
        "Autonomous loop complete: %d processed, %d errors",
        result["processed"], result["errors"],
    )
    log_to_vault(
        "autonomous_loop_completed",
        "autonomous_loop",
        "success",
        processed=str(result["processed"]),
        errors=str(result["errors"]),
    )

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    result = run_autonomous_loop()
    print(f"\nAutonomous loop result: {result['processed']} processed, {result['errors']} errors")
    for r in result.get("results", []):
        status = r.get("status", "unknown")
        print(f"  - {r.get('file', '?')}: {status}")


if __name__ == "__main__":
    main()
