# Gold Tier AI Employee — Sharmeen Asif

> **Hackathon:** GIAIC / Panaversity Personal AI Employee Hackathon 0
> **Owner:** Sharmeen Asif (@shery123pk)
> **Tier:** Gold — Full Autonomous Employee (5 AI Agents + 5 Watchers + 4 MCP + Autonomous Loop)

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Claude Code (Orchestrator)               │
│  Skills (13): vault · watcher · processing · approval ·     │
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
- **File:** Drop in `Inbox/` → Watcher → `Needs_Action/` → Agent processes → `Done/`
- **Email:** Gmail poll → `Needs_Action/` → EmailAgent analyses → Plan → Process → `Done/`
- **Sensitive:** Action → `Pending_Approval/` → Human → `Approved/`/`Rejected/` → Execute/Log → `Done/`
- **Autonomous:** Orchestrator scans `Needs_Action/` → TaskOptimizer prioritises → Route to agent → `Done/`
- **Finance:** CSV in `Finance/` → FinanceWatcher parses → Anomalies → `Needs_Action/`

## Vault Structure

| Folder | Purpose |
|--------|---------|
| `AI_Employee_Vault/Inbox/` | File watcher monitors this directory |
| `AI_Employee_Vault/Needs_Action/` | Action items pending processing |
| `AI_Employee_Vault/Done/` | Completed items archive |
| `AI_Employee_Vault/Plans/` | Structured execution plans + Eisenhower Matrix |
| `AI_Employee_Vault/Pending_Approval/` | Sensitive actions awaiting human review |
| `AI_Employee_Vault/Approved/` | Human-approved actions |
| `AI_Employee_Vault/Rejected/` | Human-rejected actions |
| `AI_Employee_Vault/Logs/` | Daily JSON logs + LLM usage tracking |
| `AI_Employee_Vault/Briefings/` | Daily + weekly intelligence briefings (Gold) |
| `AI_Employee_Vault/Knowledge_Base/` | Research summaries (Gold) |
| `AI_Employee_Vault/Finance/` | CSV transaction monitoring (Gold) |
| `AI_Employee_Vault/Dashboard.md` | Real-time status overview |
| `AI_Employee_Vault/Company_Handbook.md` | Operational rules & policies |

## AI Agents (5 total — Gold)

| Agent | Module | Purpose |
|-------|--------|---------|
| **EmailAgent** | `agents/email_agent.py` | Sentiment analysis, priority suggestion, auto-response drafts |
| **ResearchAgent** | `agents/research_agent.py` | Deep research, summarisation, Knowledge Base building |
| **MeetingAgent** | `agents/meeting_agent.py` | Agenda preparation, action item extraction |
| **TaskOptimizer** | `agents/task_optimizer.py` | Eisenhower Matrix prioritisation |
| **OrchestratorAgent** | `agents/orchestrator.py` | Agent coordination, autonomous loop, briefings |

All agents extend `BaseAgent` (`agents/base_agent.py`) and use OpenAI gpt-4o-mini via `agents/llm_gateway.py`.

## Agent Skills (13 total)

### Bronze Tier
1. **vault-management** — Read/write vault files, list directories, move files, update Dashboard
2. **watcher-management** — Start/stop file watcher, check status, view logs
3. **file-processing** — Process Needs_Action items, parse metadata, archive to Done, log actions

### Silver Tier
4. **approval-management** — Human-in-the-loop approval for sensitive actions (email, LinkedIn, delete)
5. **linkedin-posting** — Generate professional content and post to LinkedIn via approval workflow
6. **planning** — Analyse action items and create structured execution plans with reasoning
7. **scheduling** — Manage APScheduler periodic jobs (7 jobs total)
8. **email-management** — Search, read, send, draft emails via FastMCP server (4 tools)

### Gold Tier
9. **email-intelligence** — AI-powered email sentiment analysis and auto-response drafts
10. **research** — Deep research with LLM summarisation, Knowledge Base building
11. **meeting-prep** — Meeting agenda preparation and follow-up action items
12. **task-optimization** — Eisenhower Matrix prioritisation and workload balancing
13. **orchestration** — Autonomous agent coordination and task execution loop

## MCP Servers (4 total)

### Email Server
Register: `claude mcp add email-server -- python scripts/mcp_email_server.py`

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `search_emails` | Search Gmail by query | No |
| `read_email` | Read full email content | No |
| `send_email` | Send email (creates approval request) | Yes |
| `draft_email` | Create Gmail draft | No |

### Calendar Server (Gold)
Register: `claude mcp add calendar-server -- python scripts/mcp_calendar_server.py`

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `create_event` | Create calendar event | No |
| `list_events` | List events for date range | No |
| `update_event` | Update existing event | No |
| `delete_event` | Delete event | Yes |

### Task Server (Gold)
Register: `claude mcp add task-server -- python scripts/mcp_task_server.py`

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `create_task` | Create task in Needs_Action/ | No |
| `list_tasks` | List tasks from vault folders | No |
| `update_task` | Update task metadata | No |
| `optimize_tasks` | Run Eisenhower Matrix | No |

### Social Server (Gold)
Register: `claude mcp add social-server -- python scripts/mcp_social_server.py`

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `post_linkedin` | Post to LinkedIn | Yes |
| `post_twitter` | Post to Twitter/X | Yes |
| `schedule_post` | Schedule future post | Yes |

## Code Standards

- Python 3.13+
- UTF-8 encoding everywhere
- ISO 8601 timestamps
- All logs as structured JSON
- No hardcoded secrets — use `.env`
- Sensitive actions require human approval
- All watchers extend `BaseWatcher` abstract class

---

# Claude Code Rules (SpecKit Plus)

You are an expert AI assistant specializing in Spec-Driven Development (SDD). Your primary goal is to work with the architext to build products.

## Task context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps. 

## Default policies (must follow)
- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution contract for every request
1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum acceptance criteria
- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

## Architect Guidelines (for planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. Scope and Dependencies:
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. Key Decisions and Rationale:
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. Interfaces and API Contracts:
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. Non-Functional Requirements (NFRs) and Budgets:
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. Data Management and Migration:
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. Operational Readiness:
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. Risk Analysis and Mitigation:
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. Evaluation and Validation:
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. Architectural Decision Record (ADR):
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

## Basic Project Structure

- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks with cases
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records
- `.specify/` — SpecKit Plus templates and scripts

## Code Standards
See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.
