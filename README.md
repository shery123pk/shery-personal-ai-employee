# Gold Tier AI Employee

> **GIAIC / Panaversity Personal AI Employee Hackathon 0**
> **Owner:** Sharmeen Asif (@shery123pk)

A Gold Tier Personal AI Employee with 5 AI agents (LLM-powered), 5 watchers, 4 MCP servers, autonomous task execution loop, daily/weekly CEO briefings, Eisenhower Matrix prioritisation, and self-healing capabilities. Built with Claude Code as the AI orchestrator, an Obsidian-compatible vault, and Python.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Claude Code (Orchestrator)               │
│  Skills: vault · watcher · processing · approval ·           │
│    linkedin · planning · scheduling · email · research ·     │
│    meeting-prep · task-optimization · orchestration ·        │
│    email-intelligence                                        │
└──┬────────┬────────┬────────┬────────┬──────────────────────┘
   │        │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──────────────────────┐
│File │ │Gmail│ │Appr.│ │Proc.│ │Finance  │  4 MCP Servers │
│Watch│ │Watch│ │Watch│ │Watch│ │Watcher  │  Email·Calendar│
│(dog)│ │(API)│ │(dog)│ │(dog)│ │(CSV)    │  Task·Social   │
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬─────┘────────────────┘
   │       │       │       │       │
   └───────┴───────▼───────┴───────┘
             Obsidian Vault
   ┌────────────────────────────────┐
   │  Inbox/  Needs_Action/  Done/  │
   │  Plans/  Pending_Approval/     │
   │  Approved/  Rejected/  Logs/   │
   │  Briefings/  Knowledge_Base/   │
   │  Finance/  Dashboard.md        │
   └────────────────────────────────┘

   ┌────────────────────────────────┐
   │         5 AI Agents            │
   │  Email · Research · Meeting    │
   │  TaskOptimizer · Orchestrator  │
   │  (OpenAI gpt-4o-mini)         │
   └────────────────────────────────┘
```

**Data Flow:**
- **File:** Drop in `Inbox/` → Watcher detects → `Needs_Action/` → Agent processes → `Done/`
- **Email:** Gmail poll → `Needs_Action/` → EmailAgent analyses → Plan → Process → `Done/`
- **Sensitive:** Action → `Pending_Approval/` → Human moves to `Approved/` or `Rejected/` → Execute/Log → `Done/`
- **Autonomous:** Orchestrator scans `Needs_Action/` → TaskOptimizer prioritises → Route to agent → Execute → `Done/`
- **Finance:** CSV in `Finance/` → FinanceWatcher parses → Anomalies → `Needs_Action/`

## Setup

### Prerequisites

- Python 3.13+
- Claude Code CLI
- Git
- OpenAI API key (for Gold tier AI agents — optional, DEV_MODE available)
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
# Edit .env with your API keys
```

### OpenAI Setup (Gold Tier)

1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-your-key
   OPENAI_MODEL=gpt-4o-mini
   DEV_MODE=false
   ```
3. Or use `DEV_MODE=true` for synthetic responses (no API costs)

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
claude mcp add calendar-server -- python scripts/mcp_calendar_server.py
claude mcp add task-server -- python scripts/mcp_task_server.py
claude mcp add social-server -- python scripts/mcp_social_server.py
```

## Usage

### Gold Commands

```
/start-gold          — Launch full Gold orchestrator (all watchers + agents)
/gold-briefing       — Generate daily intelligence briefing
/weekly-briefing     — Generate CEO weekly strategic briefing
/deep-research       — Run ResearchAgent on a topic
/optimize-tasks      — Run Eisenhower Matrix prioritisation
/health-check        — Run system health report
```

### Start All Watchers

```bash
# File watcher (monitors Inbox/)
python scripts/file_watcher.py

# Gmail watcher (polls Gmail API)
python scripts/gmail_watcher.py

# Approval watcher (monitors Approved/ and Rejected/)
python scripts/approval_watcher.py

# Process watcher (system health monitoring)
python scripts/process_watcher.py

# Finance watcher (CSV transaction monitoring)
python scripts/finance_watcher.py

# Or use the scheduler to run everything periodically (7 jobs)
python scripts/scheduler.py
```

### Autonomous Loop

```bash
python scripts/autonomous_loop.py
```

The autonomous loop scans `Needs_Action/`, prioritises tasks via the Eisenhower Matrix, routes each to the appropriate AI agent, and archives completed items to `Done/`.

## AI Agents (5 total)

| Agent | Purpose |
|-------|---------|
| **EmailAgent** | Email sentiment analysis, priority suggestion, auto-response drafts |
| **ResearchAgent** | Deep research with LLM summarisation, Knowledge Base building |
| **MeetingAgent** | Meeting agenda preparation, action item extraction |
| **TaskOptimizer** | Eisenhower Matrix prioritisation (DO_FIRST/SCHEDULE/DELEGATE/ELIMINATE) |
| **OrchestratorAgent** | Agent coordination, autonomous loop, daily/weekly briefings |

All agents extend `BaseAgent` and use OpenAI gpt-4o-mini via the shared LLM gateway. DEV_MODE provides synthetic responses for zero-cost testing.

## Agent Skills (13 total)

| Skill | Tier | Purpose |
|-------|------|---------|
| `vault-management` | Bronze | Read/write/move vault files, update Dashboard |
| `watcher-management` | Bronze | Start/stop file watcher, check status, view logs |
| `file-processing` | Bronze | Process Needs_Action items, archive to Done |
| `approval-management` | Silver | Human-in-the-loop approval for sensitive actions |
| `linkedin-posting` | Silver | Generate and post professional LinkedIn content |
| `planning` | Silver | Analyse actions and create structured execution plans |
| `scheduling` | Silver | Manage periodic jobs (Gmail, processing, approvals) |
| `email-management` | Silver | Search, read, send, draft emails via MCP server |
| `email-intelligence` | Gold | AI-powered email sentiment analysis and auto-response |
| `research` | Gold | Deep research with LLM summarisation |
| `meeting-prep` | Gold | Meeting agenda preparation and follow-ups |
| `task-optimization` | Gold | Eisenhower Matrix prioritisation |
| `orchestration` | Gold | Autonomous agent coordination and task loop |

## MCP Servers (4 total)

### Email Server (Silver)
| Tool | Description | Approval |
|------|-------------|----------|
| `search_emails` | Search Gmail by query | No |
| `read_email` | Read full email content | No |
| `send_email` | Send email (creates approval) | Yes |
| `draft_email` | Create Gmail draft | No |

### Calendar Server (Gold)
| Tool | Description | Approval |
|------|-------------|----------|
| `create_event` | Create calendar event | No |
| `list_events` | List events for date range | No |
| `update_event` | Update existing event | No |
| `delete_event` | Delete event (creates approval) | Yes |

### Task Server (Gold)
| Tool | Description | Approval |
|------|-------------|----------|
| `create_task` | Create task in Needs_Action/ | No |
| `list_tasks` | List tasks from vault folders | No |
| `update_task` | Update task metadata | No |
| `optimize_tasks` | Run Eisenhower Matrix analysis | No |

### Social Server (Gold)
| Tool | Description | Approval |
|------|-------------|----------|
| `post_linkedin` | Post to LinkedIn (via approval) | Yes |
| `post_twitter` | Post to Twitter/X (via approval) | Yes |
| `schedule_post` | Schedule future social post | Yes |

## Project Structure

```
fte_silver/
├── .claude/
│   ├── commands/              ← 20 slash commands (incl. Gold commands)
│   └── skills/                ← 13 Agent Skills
├── .specify/                  ← SpecKit Plus templates & scripts
├── AI_Employee_Vault/         ← Obsidian Vault
│   ├── Inbox/                 ← Drop files here
│   ├── Needs_Action/          ← Pending action items
│   ├── Done/                  ← Completed archive
│   ├── Plans/                 ← Execution plans + Eisenhower Matrix
│   ├── Pending_Approval/      ← Awaiting human review
│   ├── Approved/              ← Human-approved actions
│   ├── Rejected/              ← Human-rejected actions
│   ├── Logs/                  ← Daily JSON logs + LLM usage
│   ├── Briefings/             ← Daily + weekly briefings (Gold)
│   ├── Knowledge_Base/        ← Research summaries (Gold)
│   ├── Finance/               ← CSV transaction monitoring (Gold)
│   ├── Dashboard.md           ← Status overview
│   └── Company_Handbook.md    ← Operational policies
├── scripts/
│   ├── agents/                ← 5 AI agents (Gold)
│   │   ├── __init__.py
│   │   ├── base_agent.py      ← BaseAgent ABC
│   │   ├── llm_gateway.py     ← OpenAI API gateway
│   │   ├── email_agent.py     ← Email analysis agent
│   │   ├── research_agent.py  ← Research agent
│   │   ├── meeting_agent.py   ← Meeting prep agent
│   │   ├── task_optimizer.py  ← Eisenhower Matrix agent
│   │   └── orchestrator.py    ← Orchestrator agent
│   ├── config.py              ← Centralized configuration
│   ├── logger.py              ← Structured logging
│   ├── file_watcher.py        ← File system watcher + BaseWatcher
│   ├── gmail_auth.py          ← Gmail OAuth module
│   ├── gmail_watcher.py       ← Gmail polling watcher
│   ├── approval_utils.py      ← Approval request creation
│   ├── approval_watcher.py    ← Approval decision watcher
│   ├── process_watcher.py     ← System health watchdog (Gold)
│   ├── finance_watcher.py     ← CSV transaction watcher (Gold)
│   ├── linkedin_poster.py     ← LinkedIn API integration
│   ├── mcp_email_server.py    ← FastMCP email server
│   ├── mcp_calendar_server.py ← FastMCP calendar server (Gold)
│   ├── mcp_task_server.py     ← FastMCP task server (Gold)
│   ├── mcp_social_server.py   ← FastMCP social server (Gold)
│   ├── scheduler.py           ← APScheduler (7 jobs)
│   ├── autonomous_loop.py     ← Autonomous execution loop (Gold)
│   ├── briefing_generator.py  ← Daily/weekly briefings (Gold)
│   └── e2e_test.py            ← Gold tier E2E tests (22 checks)
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

Runs 22 verification checks covering Bronze (6), Silver (8), and Gold (8) tier functionality.

## Hackathon Requirements

| Gold Requirement | Status | Implementation |
|------------------|--------|----------------|
| 5 specialized AI agents | Done | EmailAgent, ResearchAgent, MeetingAgent, TaskOptimizer, Orchestrator |
| LLM-powered reasoning | Done | OpenAI gpt-4o-mini via llm_gateway.py |
| 4 MCP servers | Done | Email + Calendar + Task + Social |
| 5 watchers | Done | File + Gmail + Approval + Process + Finance |
| Autonomous execution loop | Done | autonomous_loop.py with retry + prioritisation |
| Daily CEO briefing | Done | briefing_generator.py (daily + weekly) |
| Error recovery / self-healing | Done | ProcessWatchdog + RetryHandler |
| Eisenhower Matrix | Done | TaskOptimizer agent with quadrant classification |
| 13+ agent skills | Done | 8 Silver + 5 Gold skills |
| Extended e2e tests | Done | 22 checks (14 Silver + 8 Gold) |

## License

Built for the GIAIC / Panaversity Personal AI Employee Hackathon 0.
