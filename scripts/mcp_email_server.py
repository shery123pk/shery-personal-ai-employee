"""MCP Email Server — FastMCP stdio server with Gmail tools.

Provides 4 tools for Claude Code to interact with Gmail:
- search_emails: Read-only Gmail search
- read_email: Read full email content
- send_email: Creates approval request (does NOT send directly)
- draft_email: Creates Gmail draft (safe, no approval needed)

Registration:
    claude mcp add email-server -- python scripts/mcp_email_server.py

Usage:
    python scripts/mcp_email_server.py
"""

import base64
import sys
from email.mime.text import MIMEText
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))

mcp = FastMCP("email-server")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_emails(query: str, max_results: int = 10) -> str:
    """Search Gmail for emails matching a query.

    Args:
        query: Gmail search query (e.g. "from:boss subject:urgent").
        max_results: Maximum number of results to return (default 10).

    Returns:
        Formatted list of matching emails with subject, from, date, and snippet.
    """
    from gmail_auth import get_gmail_service

    service = get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return f"No emails found for query: {query}"

    output_lines = [f"Found {len(messages)} email(s) for query: {query}\n"]

    for msg_stub in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_stub["id"], format="metadata",
                 metadataHeaders=["Subject", "From", "Date"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        snippet = msg.get("snippet", "")

        output_lines.append(
            f"- **ID:** {msg_stub['id']}\n"
            f"  **Subject:** {headers.get('Subject', '(no subject)')}\n"
            f"  **From:** {headers.get('From', 'unknown')}\n"
            f"  **Date:** {headers.get('Date', '')}\n"
            f"  **Preview:** {snippet[:120]}...\n"
        )

    return "\n".join(output_lines)


@mcp.tool()
def read_email(message_id: str) -> str:
    """Read the full content of a specific email by its ID.

    Args:
        message_id: Gmail message ID (from search_emails results).

    Returns:
        Full email content with headers and body.
    """
    from gmail_auth import get_gmail_service

    service = get_gmail_service()
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

    # Extract body
    body = ""
    payload = msg.get("payload", {})

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return (
        f"**Subject:** {headers.get('Subject', '(no subject)')}\n"
        f"**From:** {headers.get('From', 'unknown')}\n"
        f"**To:** {headers.get('To', 'unknown')}\n"
        f"**Date:** {headers.get('Date', '')}\n"
        f"\n---\n\n"
        f"{body or '(no text body found)'}"
    )


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Request to send an email (requires human approval).

    This does NOT send the email directly. Instead, it creates an approval
    request in Pending_Approval/. A human must move the file to Approved/
    for the email to actually be sent.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text.

    Returns:
        Confirmation that the approval request was created.
    """
    from approval_utils import create_approval_request

    filepath = create_approval_request(
        action_type="send_email",
        summary=f"Send email to {to}: {subject}",
        details={
            "to": to,
            "subject": subject,
            "body": body,
        },
    )

    return (
        f"Approval request created for sending email.\n"
        f"- **To:** {to}\n"
        f"- **Subject:** {subject}\n"
        f"- **File:** {filepath.name}\n\n"
        f"Move the file from `Pending_Approval/` to `Approved/` to send."
    )


@mcp.tool()
def draft_email(to: str, subject: str, body: str) -> str:
    """Create a Gmail draft (safe, no approval needed).

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text.

    Returns:
        Confirmation with the draft ID.
    """
    from gmail_auth import get_gmail_service

    service = get_gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )

    return (
        f"Draft created successfully.\n"
        f"- **Draft ID:** {draft['id']}\n"
        f"- **To:** {to}\n"
        f"- **Subject:** {subject}\n\n"
        f"You can find it in your Gmail Drafts folder."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
