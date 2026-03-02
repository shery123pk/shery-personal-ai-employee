"""MCP Social Media Server — FastMCP stdio server with social posting tools.

Provides 3 tools for Claude Code to manage social media posts.
All posts route through the approval workflow.

Registration:
    claude mcp add social-server -- python scripts/mcp_social_server.py

Usage:
    python scripts/mcp_social_server.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DEV_MODE, PENDING_APPROVAL_DIR
from logger import iso_now, log_to_vault

mcp = FastMCP("social-server")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def post_linkedin(content: str) -> str:
    """Post content to LinkedIn (routes through approval workflow).

    Args:
        content: The text content to post on LinkedIn.

    Returns:
        Confirmation that the approval request was created.
    """
    from linkedin_poster import create_linkedin_post_request

    filepath = create_linkedin_post_request(content)
    return (
        f"LinkedIn post approval request created.\n"
        f"- **Content:** {content[:100]}...\n"
        f"- **File:** {filepath.name}\n\n"
        f"Move from `Pending_Approval/` to `Approved/` to publish."
    )


@mcp.tool()
def post_twitter(content: str) -> str:
    """Post content to Twitter/X (routes through approval workflow).

    In DEV_MODE, creates a dry-run approval request.

    Args:
        content: The tweet content (max 280 characters).

    Returns:
        Confirmation that the approval request was created.
    """
    from approval_utils import create_approval_request

    filepath = create_approval_request(
        action_type="post_twitter",
        summary=f"Post to Twitter: {content[:60]}...",
        details={
            "content": content[:280],
            "platform": "twitter",
            "char_count": str(len(content)),
            "dry_run": str(DEV_MODE),
        },
    )

    log_to_vault("twitter_post_request", "social_server", "approval_requested")

    return (
        f"Twitter post approval request created.\n"
        f"- **Content:** {content[:100]}...\n"
        f"- **Characters:** {len(content)}/280\n"
        f"- **File:** {filepath.name}\n"
        f"- **Mode:** {'DEV_MODE (dry-run)' if DEV_MODE else 'LIVE'}\n\n"
        f"Move from `Pending_Approval/` to `Approved/` to publish."
    )


@mcp.tool()
def schedule_post(platform: str, content: str, scheduled_time: str) -> str:
    """Schedule a social media post for future publishing.

    Creates a scheduled post file that the scheduler will pick up
    at the specified time.

    Args:
        platform: Target platform (linkedin, twitter).
        content: The post content.
        scheduled_time: When to publish (ISO 8601, e.g. '2026-03-03T10:00:00').

    Returns:
        Confirmation with the scheduled post details.
    """
    PENDING_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)

    slug = platform.lower()[:10]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"SCHEDULED_{slug}_{ts}.md"
    path = PENDING_APPROVAL_DIR / filename

    file_content = (
        f"# Scheduled Social Post\n\n"
        f"- **action_type:** schedule_post\n"
        f"- **platform:** {platform}\n"
        f"- **scheduled_time:** {scheduled_time}\n"
        f"- **status:** pending_approval\n"
        f"- **created_at:** {iso_now()}\n\n"
        f"## Content\n\n"
        f"{content}\n\n"
        f"---\n\n"
        f"Move to `Approved/` to confirm scheduling.\n"
    )

    path.write_text(file_content, encoding="utf-8")
    log_to_vault("schedule_post_request", "social_server", "approval_requested", platform=platform)

    return (
        f"Scheduled post approval request created.\n"
        f"- **Platform:** {platform}\n"
        f"- **Scheduled for:** {scheduled_time}\n"
        f"- **File:** {filename}\n\n"
        f"Move from `Pending_Approval/` to `Approved/` to confirm."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
