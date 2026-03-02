"""Research Agent — multi-source research with LLM summarisation.

Generates research summaries and saves them to Knowledge_Base/.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.base_agent import BaseAgent
from config import KNOWLEDGE_BASE_DIR

_SYSTEM_PROMPT = (
    "You are a thorough research analyst. Given a topic, provide a structured "
    "research summary with: key_findings (3-5 bullet points), detailed_summary "
    "(2-3 paragraphs), sources_suggested (relevant areas to explore), and "
    "recommendations (actionable next steps). Format as markdown."
)


class ResearchAgent(BaseAgent):
    """Multi-source research with summarisation."""

    def __init__(self) -> None:
        super().__init__(name="research_agent", system_prompt=_SYSTEM_PROMPT)

    def execute(self, task: dict) -> dict:
        """Run research on a given topic.

        Args:
            task: {"topic": str, "context": str (optional)}

        Returns:
            {"summary": str, "key_findings": str,
             "output_path": str | None}
        """
        topic = task.get("topic", "")
        context = task.get("context", "")

        prompt = f"Research topic: {topic}"
        if context:
            prompt += f"\n\nAdditional context: {context}"
        prompt += "\n\nProvide a comprehensive research summary in markdown."

        response = self.call_llm(prompt, max_tokens=800)

        # Save to Knowledge_Base
        output_path = self._save_summary(topic, response)

        self.log_action("research_completed", "success", topic=topic[:60])

        return {
            "summary": response,
            "key_findings": self._extract_findings(response),
            "output_path": str(output_path) if output_path else None,
        }

    def summarize(self, content: str, max_length: int = 500) -> str:
        """LLM-powered summarisation of arbitrary content."""
        prompt = (
            f"Summarise the following content in {max_length} characters or fewer:\n\n"
            f"{content[:3000]}"
        )
        return self.call_llm(prompt, max_tokens=400)

    def _save_summary(self, topic: str, content: str) -> Path | None:
        """Save research summary to Knowledge_Base/."""
        try:
            KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
            slug = topic.lower().replace(" ", "_")[:40]
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            filename = f"research_{slug}_{date}.md"
            path = KNOWLEDGE_BASE_DIR / filename

            header = (
                f"# Research: {topic}\n\n"
                f"> Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n"
                "---\n\n"
            )
            path.write_text(header + content, encoding="utf-8")
            return path
        except OSError:
            return None

    @staticmethod
    def _extract_findings(text: str) -> str:
        """Extract key findings section from markdown response."""
        lines = text.split("\n")
        findings = []
        in_findings = False
        for line in lines:
            if "finding" in line.lower() or "key" in line.lower() and "#" in line:
                in_findings = True
                continue
            if in_findings:
                if line.startswith("#"):
                    break
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    findings.append(line.strip())
        return "\n".join(findings) if findings else text[:300]
