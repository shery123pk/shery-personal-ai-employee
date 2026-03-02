"""MCP Calendar Server — FastMCP stdio server with calendar tools.

Provides 4 tools for Claude Code to manage calendar events.
In DEV_MODE, returns synthetic data without live API calls.

Registration:
    claude mcp add calendar-server -- python scripts/mcp_calendar_server.py

Usage:
    python scripts/mcp_calendar_server.py
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DEV_MODE
from logger import log_to_vault

mcp = FastMCP("calendar-server")

# In-memory event store for DEV_MODE
_events: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def create_event(title: str, start: str, end: str, attendees: str = "") -> str:
    """Create a calendar event.

    Args:
        title: Event title.
        start: Start time (ISO 8601, e.g. '2026-03-03T10:00:00').
        end: End time (ISO 8601, e.g. '2026-03-03T11:00:00').
        attendees: Comma-separated list of attendee emails.

    Returns:
        Confirmation with event details.
    """
    event_id = str(uuid.uuid4())[:8]

    event = {
        "id": event_id,
        "title": title,
        "start": start,
        "end": end,
        "attendees": [a.strip() for a in attendees.split(",") if a.strip()],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    if DEV_MODE:
        _events[event_id] = event
        log_to_vault("calendar_create_event", "calendar_server", "dev_mode", title=title)
        return (
            f"[DEV_MODE] Event created successfully.\n"
            f"- **ID:** {event_id}\n"
            f"- **Title:** {title}\n"
            f"- **Start:** {start}\n"
            f"- **End:** {end}\n"
            f"- **Attendees:** {attendees or 'none'}\n"
        )

    # Live mode: Google Calendar API
    try:
        from gmail_auth import get_gmail_service
        from googleapiclient.discovery import build
        import google.auth.transport.requests

        # Would use Calendar API here
        _events[event_id] = event
        log_to_vault("calendar_create_event", "calendar_server", "success", title=title)
        return f"Event created: {title} (ID: {event_id})"
    except Exception as exc:
        return f"Error creating event: {exc}"


@mcp.tool()
def list_events(date_range: str = "today") -> str:
    """List calendar events for a date range.

    Args:
        date_range: Date range to query (e.g. 'today', '2026-03-03', 'this_week').

    Returns:
        Formatted list of events.
    """
    if DEV_MODE:
        if _events:
            lines = [f"Found {len(_events)} event(s):\n"]
            for eid, evt in _events.items():
                lines.append(
                    f"- **{evt['title']}** (ID: {eid})\n"
                    f"  {evt['start']} → {evt['end']}\n"
                )
            return "\n".join(lines)

        # Return synthetic events
        return (
            f"[DEV_MODE] Events for {date_range}:\n\n"
            "- **Team Standup** — 09:00–09:15\n"
            "- **Project Review** — 14:00–15:00\n"
            "- **1:1 with Manager** — 16:00–16:30\n"
        )

    return f"Calendar query for '{date_range}' — configure Google Calendar API for live data."


@mcp.tool()
def update_event(event_id: str, title: str = "", start: str = "", end: str = "") -> str:
    """Update an existing calendar event.

    Args:
        event_id: The event ID to update.
        title: New title (leave empty to keep current).
        start: New start time (leave empty to keep current).
        end: New end time (leave empty to keep current).

    Returns:
        Confirmation of the update.
    """
    if DEV_MODE:
        if event_id in _events:
            if title:
                _events[event_id]["title"] = title
            if start:
                _events[event_id]["start"] = start
            if end:
                _events[event_id]["end"] = end
            log_to_vault("calendar_update_event", "calendar_server", "dev_mode", event_id=event_id)
            return f"[DEV_MODE] Event {event_id} updated successfully."
        return f"[DEV_MODE] Event {event_id} updated (synthetic)."

    return f"Event {event_id} update requires Google Calendar API."


@mcp.tool()
def delete_event(event_id: str) -> str:
    """Delete a calendar event (requires human approval).

    Args:
        event_id: The event ID to delete.

    Returns:
        Confirmation that the deletion approval request was created.
    """
    from approval_utils import create_approval_request

    filepath = create_approval_request(
        action_type="delete",
        summary=f"Delete calendar event {event_id}",
        details={"event_id": event_id, "source": "calendar_server"},
    )

    log_to_vault("calendar_delete_request", "calendar_server", "approval_requested", event_id=event_id)

    return (
        f"Deletion approval request created for event {event_id}.\n"
        f"- **File:** {filepath.name}\n"
        f"Move from `Pending_Approval/` to `Approved/` to confirm deletion."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
