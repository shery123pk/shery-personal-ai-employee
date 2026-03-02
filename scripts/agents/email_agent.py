"""Email Agent — analyses emails for sentiment, priority, and drafts responses.

Uses LLM to provide intelligent email triage and auto-response suggestions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.base_agent import BaseAgent

_SYSTEM_PROMPT = (
    "You are an expert email analyst. Analyse the email and return "
    "a JSON object with keys: sentiment (positive/negative/neutral/urgent), "
    "priority_suggestion (URGENT/REVIEW/FYI), summary (1-2 sentences), "
    "and draft_reply (a professional reply draft). Keep it concise."
)


class EmailAgent(BaseAgent):
    """Analyses emails: sentiment, priority, auto-response drafts."""

    def __init__(self) -> None:
        super().__init__(name="email_agent", system_prompt=_SYSTEM_PROMPT)

    def execute(self, task: dict) -> dict:
        """Analyse an email action item.

        Args:
            task: {"content": str, "source": str, "subject": str}

        Returns:
            {"sentiment": str, "priority_suggestion": str,
             "summary": str, "draft_reply": str}
        """
        email_text = task.get("content", "")
        subject = task.get("subject", "unknown")

        prompt = (
            f"Subject: {subject}\n\n"
            f"Email body:\n{email_text}\n\n"
            "Analyse this email and provide your JSON response."
        )
        response = self.call_llm(prompt)

        self.log_action("email_analysis", "success", subject=subject)

        return {
            "sentiment": self._extract_field(response, "sentiment", "neutral"),
            "priority_suggestion": self._extract_field(response, "priority_suggestion", "REVIEW"),
            "summary": self._extract_field(response, "summary", response[:200]),
            "draft_reply": self._extract_field(response, "draft_reply", ""),
            "raw_analysis": response,
        }

    def analyze_sentiment(self, email_text: str) -> str:
        """Return sentiment: positive, negative, neutral, or urgent."""
        prompt = f"Classify the sentiment of this email as one word (positive/negative/neutral/urgent):\n\n{email_text}"
        return self.call_llm(prompt, max_tokens=20).strip().lower()

    def draft_response(self, email_text: str, context: str = "") -> str:
        """Generate a context-aware email reply draft."""
        prompt = (
            f"Write a professional reply to this email.\n\n"
            f"Email:\n{email_text}\n\n"
            f"Context: {context or 'none'}\n\n"
            "Reply:"
        )
        return self.call_llm(prompt, max_tokens=500)

    @staticmethod
    def _extract_field(text: str, field: str, default: str) -> str:
        """Try to extract a JSON field from LLM response text."""
        import json
        try:
            # Try direct JSON parse
            data = json.loads(text)
            return data.get(field, default)
        except (json.JSONDecodeError, TypeError):
            pass
        # Fallback: look for "field": "value" pattern
        import re
        pattern = rf'"{field}"\s*:\s*"([^"]*)"'
        match = re.search(pattern, text)
        return match.group(1) if match else default
