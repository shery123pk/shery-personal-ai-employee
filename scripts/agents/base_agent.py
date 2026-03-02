"""Abstract base class for all Gold-tier AI agents.

Every agent extends BaseAgent and implements execute().
The base class provides LLM integration via llm_gateway and
structured logging to the vault.
"""

import abc
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.llm_gateway import call_openai
from logger import log_to_vault, setup_console_logger


class BaseAgent(abc.ABC):
    """Abstract base class for all Gold-tier AI agents."""

    def __init__(self, name: str, system_prompt: str) -> None:
        self.name = name
        self.system_prompt = system_prompt

    @abc.abstractmethod
    def execute(self, task: dict) -> dict:
        """Execute the agent's main task.

        Args:
            task: Task descriptor dict (varies per agent).

        Returns:
            Result dict with agent-specific output.
        """

    def call_llm(self, user_prompt: str, max_tokens: int | None = None) -> str:
        """Call OpenAI via the shared gateway.

        Args:
            user_prompt: The task-specific prompt.
            max_tokens: Optional override for max output tokens.

        Returns:
            LLM response text.
        """
        result = call_openai(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )
        return result["text"]

    def log_action(self, action: str, result: str, **extra: str) -> None:
        """Log an agent action to the vault."""
        log_to_vault(
            action=f"agent_{action}",
            source=self.name,
            result=result,
            **extra,
        )
        logger = setup_console_logger(self.name)
        logger.info("[%s] %s → %s", self.name, action, result)
