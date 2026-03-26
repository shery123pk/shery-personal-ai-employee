"""Cloud Agent — handles Cloud-zone tasks (triage, drafting, research).

The Cloud agent can analyse emails and draft replies, generate social
post content, and schedule research — but it CANNOT send emails, post
to social media, or make payments. All actionable outputs are written
to Pending_Approval/<domain>/ for Local zone approval.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.base_agent import BaseAgent
from config import PENDING_APPROVAL_DIR
from logger import iso_now

_SYSTEM_PROMPT = (
    "You are a cloud AI assistant that triages emails and drafts responses. "
    "You analyse content, identify priority and sentiment, and generate "
    "professional reply drafts. You NEVER send emails or post directly — "
    "all outputs require human approval."
)


class CloudAgent(BaseAgent):
    """Cloud-zone agent for email triage, social drafts, and research."""

    def __init__(self) -> None:
        super().__init__(name="cloud_agent", system_prompt=_SYSTEM_PROMPT)

    def execute(self, task: dict) -> dict:
        """Route to the appropriate cloud sub-task.

        Args:
            task: {"content": str, "action": str, ...}

        Returns:
            {"action": str, "result": dict}
        """
        action = task.get("action", "email_triage")

        if action == "email_triage":
            return self.triage_email(task)
        elif action in ("social_draft", "social_schedule"):
            return self.draft_social_post(task)
        else:
            return self.triage_email(task)

    def triage_email(self, task: dict) -> dict:
        """Analyse an email, classify priority/sentiment, and draft a reply.

        Writes an approval file to Pending_Approval/email/ for Local review.

        Returns:
            {"action": "email_triage", "priority": str, "sentiment": str, "draft": str, "approval_file": str}
        """
        content = task.get("content", "")
        subject = task.get("subject", "Email")

        prompt = (
            f"Analyse this email and provide:\n"
            f"1. Priority (URGENT/REVIEW/FYI)\n"
            f"2. Sentiment (positive/neutral/negative)\n"
            f"3. A professional reply draft\n\n"
            f"Email:\n{content[:2000]}"
        )
        analysis = self.call_llm(prompt, max_tokens=500)

        # Write approval file for the draft reply
        approval_dir = PENDING_APPROVAL_DIR / "email"
        approval_dir.mkdir(parents=True, exist_ok=True)

        timestamp = iso_now()
        filename = f"APPROVE_email_reply_{timestamp.replace(':', '-')}.md"
        filepath = approval_dir / filename

        approval_content = (
            f"# Approval Request: Email Reply Draft\n\n"
            f"- **action_type:** send_email\n"
            f"- **requested_at:** {timestamp}\n"
            f"- **status:** pending_approval\n"
            f"- **source:** cloud_agent\n"
            f"- **original_subject:** {subject}\n\n"
            f"## Analysis\n\n{analysis}\n\n"
            f"---\n\n"
            f"**Instructions:** Review and move to `Approved/` or `Rejected/`.\n"
        )
        filepath.write_text(approval_content, encoding="utf-8")

        self.log_action("email_triage", "success", subject=subject, approval_file=filename)
        return {
            "action": "email_triage",
            "priority": "REVIEW",
            "sentiment": "neutral",
            "draft": analysis,
            "approval_file": filename,
        }

    def draft_social_post(self, task: dict) -> dict:
        """Generate social media content and write an approval file.

        Returns:
            {"action": "social_draft", "content": str, "approval_file": str}
        """
        topic = task.get("content", "company update")

        prompt = (
            f"Write a professional LinkedIn post about: {topic[:500]}\n"
            f"Keep it under 280 characters for cross-platform compatibility."
        )
        draft = self.call_llm(prompt, max_tokens=200)

        approval_dir = PENDING_APPROVAL_DIR / "social"
        approval_dir.mkdir(parents=True, exist_ok=True)

        timestamp = iso_now()
        filename = f"APPROVE_social_post_{timestamp.replace(':', '-')}.md"
        filepath = approval_dir / filename

        approval_content = (
            f"# Approval Request: Social Media Post\n\n"
            f"- **action_type:** post_linkedin\n"
            f"- **requested_at:** {timestamp}\n"
            f"- **status:** pending_approval\n"
            f"- **source:** cloud_agent\n\n"
            f"## Draft Content\n\n{draft}\n\n"
            f"---\n\n"
            f"**Instructions:** Review and move to `Approved/` or `Rejected/`.\n"
        )
        filepath.write_text(approval_content, encoding="utf-8")

        self.log_action("social_draft", "success", approval_file=filename)
        return {
            "action": "social_draft",
            "content": draft,
            "approval_file": filename,
        }
