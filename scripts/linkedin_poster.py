"""LinkedIn posting module — creates posts via LinkedIn API v2.

All posts go through the approval workflow first.
Supports dry-run mode when no access token is configured.

Setup:
    1. Go to https://www.linkedin.com/developers/
    2. Create an app and request r_liteprofile + w_member_social permissions
    3. Generate an access token
    4. Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN in .env
"""

import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import LINKEDIN_ACCESS_TOKEN, LINKEDIN_DRY_RUN, LINKEDIN_PERSON_URN
from logger import log_to_vault, setup_console_logger

logger = setup_console_logger("linkedin")

LINKEDIN_API_URL = "https://api.linkedin.com/v2/ugcPosts"


def create_linkedin_post_request(content: str) -> Path:
    """Create an approval request for a LinkedIn post.

    Args:
        content: The text content to post on LinkedIn.

    Returns:
        Path to the approval request file.
    """
    from approval_utils import create_approval_request

    filepath = create_approval_request(
        action_type="post_linkedin",
        summary=f"Post to LinkedIn: {content[:60]}...",
        details={
            "content": content,
            "platform": "linkedin",
            "person_urn": LINKEDIN_PERSON_URN or "(not configured)",
            "dry_run": str(LINKEDIN_DRY_RUN),
        },
    )

    logger.info("LinkedIn post approval request created: %s", filepath.name)
    return filepath


def publish_to_linkedin(content: str, access_token: str = "") -> str:
    """Publish a post to LinkedIn via the API.

    Only called after approval. Falls back to dry-run mode if no token.

    Args:
        content: The text content to post.
        access_token: LinkedIn OAuth access token.

    Returns:
        Result string describing what happened.
    """
    token = access_token or LINKEDIN_ACCESS_TOKEN

    if not token or LINKEDIN_DRY_RUN:
        result = f"[DRY RUN] LinkedIn post would be published: {content[:100]}..."
        logger.info(result)
        log_to_vault(
            action="linkedin_post_dry_run",
            source="linkedin_poster",
            result="dry_run",
            content_preview=content[:100],
        )
        return result

    if not LINKEDIN_PERSON_URN:
        return "LinkedIn post failed: LINKEDIN_PERSON_URN not configured in .env"

    payload = {
        "author": f"urn:li:person:{LINKEDIN_PERSON_URN}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    response = requests.post(LINKEDIN_API_URL, json=payload, headers=headers, timeout=30)

    if response.status_code == 201:
        post_id = response.json().get("id", "unknown")
        result = f"LinkedIn post published successfully (ID: {post_id})"
        logger.info(result)
        log_to_vault(
            action="linkedin_post_published",
            source="linkedin_poster",
            result="success",
            post_id=post_id,
        )
    else:
        result = f"LinkedIn post failed ({response.status_code}): {response.text[:200]}"
        logger.error(result)
        log_to_vault(
            action="linkedin_post_failed",
            source="linkedin_poster",
            result="error",
            status_code=str(response.status_code),
            detail=response.text[:200],
        )

    return result


if __name__ == "__main__":
    # Quick test: create a post request (goes through approval)
    test_content = (
        "Excited to share my AI Employee project for the "
        "GIAIC/Panaversity Hackathon! Built with Claude Code, "
        "Python watchers, and an Obsidian vault. #AI #Hackathon"
    )
    path = create_linkedin_post_request(test_content)
    print(f"Approval request created: {path}")
    print("Move to Approved/ to publish, or Rejected/ to cancel.")
