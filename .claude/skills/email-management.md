---
name: email-management
description: Search, read, send, and draft emails via Gmail MCP server
priority: required
tier: silver
---

# Skill: Email Management (MCP Server)

Manage Gmail emails using the MCP email server tools.

## Capabilities

### Search emails
Use the `search_emails` MCP tool to find emails:
- Search by sender, subject, date, labels
- Returns subject, from, date, and preview for each result
- No approval required (read-only)

### Read email content
Use the `read_email` MCP tool to read full email text:
- Provide the Gmail message ID (from search results)
- Returns headers and full body content
- No approval required (read-only)

### Send email (via approval)
Use the `send_email` MCP tool:
- Creates an approval request in `Pending_Approval/`
- Does NOT send directly — requires human authorization
- Human moves to `Approved/` to send, `Rejected/` to cancel

### Draft email (safe)
Use the `draft_email` MCP tool:
- Creates a draft in Gmail Drafts folder
- No approval required (non-destructive)
- User can review and send manually from Gmail

## MCP Server Registration

```
claude mcp add email-server -- python scripts/mcp_email_server.py
```

## Usage Examples

- "Search my emails for messages from the CFO"
- "Read the latest email about the budget report"
- "Send an email to team@company.com about the meeting"
- "Draft a reply to the marketing proposal"

## Rules

- Sending emails ALWAYS requires approval — use the approval workflow
- Drafting emails is safe and does not require approval
- Search and read are read-only operations
- Gmail OAuth must be configured (see README for setup)
- All email operations are logged to vault
