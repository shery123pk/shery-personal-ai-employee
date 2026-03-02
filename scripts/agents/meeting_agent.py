"""Meeting Agent — meeting preparation and follow-up documentation.

Generates meeting agendas and extracts action items from meeting notes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.base_agent import BaseAgent

_SYSTEM_PROMPT = (
    "You are a professional meeting coordinator. You help prepare "
    "structured meeting agendas and extract clear action items from "
    "meeting notes. Always include owners, deadlines, and priorities "
    "for action items. Format output as markdown."
)


class MeetingAgent(BaseAgent):
    """Meeting preparation and follow-up documentation."""

    def __init__(self) -> None:
        super().__init__(name="meeting_agent", system_prompt=_SYSTEM_PROMPT)

    def execute(self, task: dict) -> dict:
        """Handle meeting-related tasks.

        Args:
            task: {"type": "agenda"|"followup",
                   "topic": str, "attendees": list,
                   "context": str, "notes": str}

        Returns:
            {"agenda": str, "action_items": list, "summary": str}
        """
        task_type = task.get("type", "agenda")

        if task_type == "followup":
            notes = task.get("notes", "")
            action_items = self.generate_followups(notes)
            summary = self.call_llm(
                f"Summarise these meeting notes in 2-3 sentences:\n\n{notes}",
                max_tokens=200,
            )
            self.log_action("meeting_followup", "success")
            return {"agenda": "", "action_items": action_items, "summary": summary}

        topic = task.get("topic", "General Meeting")
        attendees = task.get("attendees", [])
        context = task.get("context", "")
        agenda = self.prepare_agenda(topic, attendees, context)
        self.log_action("meeting_agenda", "success", topic=topic[:60])
        return {"agenda": agenda, "action_items": [], "summary": ""}

    def prepare_agenda(self, topic: str, attendees: list, context: str = "") -> str:
        """Generate a structured meeting agenda."""
        attendee_list = ", ".join(attendees) if attendees else "TBD"
        prompt = (
            f"Create a structured meeting agenda.\n\n"
            f"Topic: {topic}\n"
            f"Attendees: {attendee_list}\n"
            f"Context: {context or 'none'}\n\n"
            "Include: objectives, agenda items with time estimates, "
            "discussion points, and next steps section."
        )
        return self.call_llm(prompt, max_tokens=600)

    def generate_followups(self, meeting_notes: str) -> list[dict]:
        """Extract action items from meeting notes.

        Returns list of {"owner": str, "action": str, "deadline": str, "priority": str}
        """
        prompt = (
            f"Extract action items from these meeting notes. For each item, "
            f"provide: owner, action, deadline, priority (HIGH/MEDIUM/LOW).\n"
            f"Format each as a bullet point.\n\n"
            f"Notes:\n{meeting_notes}"
        )
        response = self.call_llm(prompt, max_tokens=500)

        # Parse bullet points into structured items
        items = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                items.append({
                    "owner": "TBD",
                    "action": line.lstrip("-* "),
                    "deadline": "TBD",
                    "priority": "MEDIUM",
                })
        return items if items else [{"owner": "TBD", "action": response[:200], "deadline": "TBD", "priority": "MEDIUM"}]
