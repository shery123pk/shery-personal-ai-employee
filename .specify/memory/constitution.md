<!-- Sync Impact Report
Version change: 1.0.0 → 2.0.0
Added principles: Human-in-the-Loop, Multi-Source Intelligence, Planned Execution
Updated sections: Operational Standards, Development Workflow
Removed sections: none
Templates requiring updates: all current
Follow-up TODOs: none
-->

# Shery Personal AI Employee Constitution

## Core Principles

### I. Vault-First

Every operation MUST read from and write to the Obsidian vault (`AI_Employee_Vault/`). The vault is the single source of truth for all task state. No in-memory-only state is permitted — if the agent restarts, the vault MUST reflect the last known state. Files flow through a strict pipeline: `Inbox/ → Needs_Action/ → Done/`. Sensitive actions route through: `Pending_Approval/ → Approved/Rejected/ → Done/`.

### II. Watcher Reliability

All watchers MUST detect every relevant event without exception. On startup, watchers MUST perform an initial scan to catch events that occurred while offline. All watchers extend the `BaseWatcher` abstract class to ensure consistent interface. Three watchers operate: FileSystemWatcher (Inbox), GmailWatcher (Gmail API), ApprovalWatcher (Approved/Rejected folders).

### III. Structured Logging

All events MUST be logged as structured JSON to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`. Every log entry MUST include: ISO 8601 timestamp, action name, source identifier, and result. Console logging mirrors vault logging for real-time visibility. No silent failures — errors MUST be logged before propagating.

### IV. Priority-Driven Processing

Files MUST be classified by priority keywords: URGENT (immediate), REVIEW (current session), FYI (when queue clears). Default priority is Medium. Processing order MUST respect priority: URGENT first, then REVIEW, then FYI, then Medium. Priority is determined by keyword presence in filename, content, or Gmail labels (STARRED→URGENT, IMPORTANT→REVIEW).

### V. Security by Default

No secrets, tokens, or credentials stored in vault or committed to git. All configuration MUST use environment variables via `.env`. The vault is git-tracked — assume all vault contents are public. Sensitive files MUST NOT be placed in Inbox. OAuth tokens (`token.json`, `credentials.json`) are gitignored.

### VI. Simplicity

Start with the minimum viable implementation. No premature abstractions — three similar lines are better than a premature helper. YAGNI: do not build for hypothetical future requirements. Every file and function MUST have a clear, single purpose. Prefer flat structures over deep nesting.

### VII. Human-in-the-Loop (Silver)

Sensitive actions MUST require explicit human approval before execution. The approval workflow uses file-based signaling: requests in `Pending_Approval/`, decisions via moving to `Approved/` or `Rejected/`. The agent MUST NEVER bypass the approval workflow for sensitive actions. Humans review, decide, and the system executes — never the reverse.

### VIII. Multi-Source Intelligence (Silver)

The AI Employee ingests information from multiple sources: file system (Inbox), email (Gmail API), and human input. Each source feeds into the same `Needs_Action/` pipeline with consistent metadata and priority classification. The MCP email server provides Claude with direct access to search and read emails.

### IX. Planned Execution (Silver)

Complex multi-step actions MUST be planned before execution. Plans are structured documents in `Plans/` with steps, dependencies, owners, and risks. Plans that include sensitive actions MUST route through the approval workflow. The planning skill analyzes the Needs_Action queue and creates actionable plans.

## Operational Standards

- Python 3.13+ required
- UTF-8 encoding everywhere, no exceptions
- ISO 8601 for all timestamps (`YYYY-MM-DDTHH:MM:SSZ`)
- Dashboard MUST be updated after every vault modification
- Action files use naming conventions: `FILE_[name].md`, `EMAIL_[slug].md`
- One log file per day, append-only
- Centralized config via `scripts/config.py` loading from `.env`
- All watchers extend `BaseWatcher` abstract class
- MCP server tools use FastMCP stdio protocol

## Development Workflow

- All changes go through git with descriptive commit messages
- SpecKit Plus slash commands used for spec-driven development
- Code review via pull requests when collaborating
- E2E test (`python scripts/e2e_test.py`) MUST pass before any release — 14 checks for Silver tier
- No force pushes to main/master branch

## Governance

This constitution is the authoritative guide for all development and operational decisions on the Shery Personal AI Employee project. Amendments require:
1. Documentation of the change and rationale
2. Version bump following semantic versioning (MAJOR.MINOR.PATCH)
3. Update to all dependent artifacts (CLAUDE.md, templates, README)
4. All PRs and code reviews MUST verify compliance with these principles

**Version**: 2.0.0 | **Ratified**: 2026-02-24 | **Last Amended**: 2026-02-28
