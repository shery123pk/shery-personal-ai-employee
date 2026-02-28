# Silver Tier AI Employee

> **GIAIC / Panaversity Personal AI Employee Hackathon 0**
> **Owner:** Sharmeen Asif (@shery123pk)

A Silver Tier Personal AI Employee with Gmail integration, LinkedIn posting, human-in-the-loop approval workflow, planning skill, MCP server, and scheduling. Built with Claude Code as the AI agent, an Obsidian-compatible vault, and Python watchers.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Claude Code (Agent)                 │
│  Skills: vault · watcher · processing · approval ·   │
│          linkedin · planning · scheduling · email    │
└────┬──────────┬──────────┬──────────┬───────────────┘
     │          │          │          │
┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼──────────────┐
│  File  │ │ Gmail  │ │Approval│ │   MCP Email      │
│Watcher │ │Watcher │ │Watcher │ │   Server         │
│(watch  │ │(Gmail  │ │(watch  │ │  (4 tools)       │
│ dog)   │ │ API)   │ │ dog)   │ │                  │
└───┬────┘ └───┬────┘ └───┬────┘ └──────────────────┘
    │          │          │
    └──────────▼──────────┘
         Obsidian Vault
    ┌──────────────────────┐
    │  Inbox/              │
    │  Needs_Action/       │
    │  Done/               │
    │  Plans/              │
    │  Pending_Approval/   │
    │  Approved/           │
    │  Rejected/           │
    │  Logs/               │
    │  Dashboard.md        │
    └──────────────────────┘
```

**Data Flow:**
- **File:** Drop in `Inbox/` → Watcher detects → `Needs_Action/` → Process → `Done/`
- **Email:** Gmail poll → `Needs_Action/` → Plan → Process → `Done/`
- **Sensitive:** Action → `Pending_Approval/` → Human moves to `Approved/` or `Rejected/` → Execute/Log → `Done/`

## Setup

### Prerequisites

- Python 3.13+
- Claude Code CLI
- Git
- Google Cloud project (for Gmail — optional)
- LinkedIn Developer App (for LinkedIn — optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/shery123pk/fte_silver.git
cd fte_silver

# Install Python dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

### Gmail Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Gmail API**
4. Create **OAuth 2.0 credentials** (Desktop application)
5. Download the JSON and save as `credentials.json` in project root
6. Run initial auth: `python scripts/gmail_auth.py`
7. Update `.env` with your settings

### LinkedIn Setup (Optional)

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create an app and request `r_liteprofile` + `w_member_social` permissions
3. Generate an access token
4. Add to `.env`:
   ```
   LINKEDIN_ACCESS_TOKEN=your_token
   LINKEDIN_PERSON_URN=your_urn
   LINKEDIN_DRY_RUN=false
   ```

### MCP Server Registration

```bash
claude mcp add email-server -- python scripts/mcp_email_server.py
```

## Usage

### Start All Watchers

```bash
# File watcher (monitors Inbox/)
python scripts/file_watcher.py

# Gmail watcher (polls Gmail API)
python scripts/gmail_watcher.py

# Approval watcher (monitors Approved/ and Rejected/)
python scripts/approval_watcher.py

# Or use the scheduler to run everything periodically
python scripts/scheduler.py
```

### Drop a File

Place any file in `AI_Employee_Vault/Inbox/`. The watcher will detect it, parse priority, and create an action item.

### Process with Claude

```
> Process all items in Needs_Action
> Plan how to handle today's action items
> Draft a LinkedIn post about our Q1 results
> Search my recent emails about the budget
```

### Approval Workflow

1. Agent creates approval request in `Pending_Approval/`
2. Review the file in your Obsidian vault
3. Move to `Approved/` to execute, or `Rejected/` to deny
4. Approval watcher handles the rest

## Agent Skills (8 total)

| Skill | Tier | Purpose |
|-------|------|---------|
| `vault-management` | Bronze | Read/write/move vault files, update Dashboard |
| `watcher-management` | Bronze | Start/stop file watcher, check status, view logs |
| `file-processing` | Bronze | Process Needs_Action items, archive to Done |
| `approval-management` | Silver | Human-in-the-loop approval for sensitive actions |
| `linkedin-posting` | Silver | Generate and post professional LinkedIn content |
| `planning` | Silver | Analyze actions and create structured execution plans |
| `scheduling` | Silver | Manage periodic jobs (Gmail, processing, approvals) |
| `email (MCP)` | Silver | Search, read, send, draft emails via MCP server |

## MCP Server Tools

| Tool | Description | Approval Required |
|------|-------------|-------------------|
| `search_emails` | Search Gmail by query | No |
| `read_email` | Read full email content | No |
| `send_email` | Send email (creates approval request) | Yes |
| `draft_email` | Create Gmail draft | No |

## Project Structure

```
fte_silver/
├── .claude/
│   ├── commands/              ← Slash commands (incl. /plan-actions)
│   └── skills/                ← 8 Agent Skills
├── .specify/                  ← SpecKit Plus templates & scripts
├── AI_Employee_Vault/         ← Obsidian Vault
│   ├── Inbox/                 ← Drop files here
│   ├── Needs_Action/          ← Pending action items
│   ├── Done/                  ← Completed archive
│   ├── Plans/                 ← Execution plans
│   ├── Pending_Approval/      ← Awaiting human review
│   ├── Approved/              ← Human-approved actions
│   ├── Rejected/              ← Human-rejected actions
│   ├── Logs/                  ← Daily JSON logs
│   ├── Dashboard.md           ← Status overview
│   └── Company_Handbook.md    ← Operational policies
├── scripts/
│   ├── config.py              ← Centralized configuration
│   ├── logger.py              ← Structured logging
│   ├── file_watcher.py        ← File system watcher
│   ├── gmail_auth.py          ← Gmail OAuth module
│   ├── gmail_watcher.py       ← Gmail polling watcher
│   ├── approval_utils.py      ← Approval request creation
│   ├── approval_watcher.py    ← Approval decision watcher
│   ├── linkedin_poster.py     ← LinkedIn API integration
│   ├── mcp_email_server.py    ← FastMCP email server
│   ├── scheduler.py           ← APScheduler periodic jobs
│   └── e2e_test.py            ← Silver tier E2E tests (14 checks)
├── .env.example
├── .gitignore
├── CLAUDE.md
├── README.md
└── requirements.txt
```

## Running Tests

```bash
python scripts/e2e_test.py
```

Runs 14 verification checks covering both Bronze and Silver tier functionality.

## Hackathon Requirements

| Silver Requirement | Status | Implementation |
|--------------------|--------|----------------|
| 2+ watcher scripts | Done | FileSystemWatcher + GmailWatcher + ApprovalWatcher |
| Auto-post on LinkedIn | Done | linkedin_poster.py with approval workflow |
| Claude reasoning / Plan.md | Done | planning skill + /plan-actions command |
| 1 working MCP server | Done | mcp_email_server.py (4 tools) |
| Human-in-the-loop approval | Done | Pending_Approval/ → Approved/Rejected/ workflow |
| Basic scheduling | Done | APScheduler with 4 periodic jobs |
| All AI as Agent Skills | Done | 8 skills total (3 Bronze + 5 Silver) |

## License

Built for the GIAIC / Panaversity Personal AI Employee Hackathon 0.
