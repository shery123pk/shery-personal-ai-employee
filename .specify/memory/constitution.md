<!-- Sync Impact Report
Version change: 0.0.0 → 1.0.0
Added principles: Vault-First, Watcher Reliability, Structured Logging, Priority-Driven Processing, Security by Default, Simplicity
Added sections: Operational Standards, Development Workflow
Removed sections: none
Templates requiring updates: ✅ all current
Follow-up TODOs: none
-->

# Shery Personal AI Employee Constitution

## Core Principles

### I. Vault-First

Every operation MUST read from and write to the Obsidian vault (`AI_Employee_Vault/`). The vault is the single source of truth for all task state. No in-memory-only state is permitted — if the agent restarts, the vault MUST reflect the last known state. Files flow through a strict pipeline: `Inbox/ → Needs_Action/ → Done/`.

### II. Watcher Reliability

The file system watcher MUST detect every new file in `Inbox/` without exception. On startup, the watcher MUST perform an initial scan to catch files added while it was offline. The watcher uses the `BaseWatcher` abstract class to ensure consistent interface across implementations. Only one watcher instance may run at a time.

### III. Structured Logging

All events MUST be logged as structured JSON to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`. Every log entry MUST include: ISO 8601 timestamp, action name, source identifier, and result. Console logging mirrors vault logging for real-time visibility. No silent failures — errors MUST be logged before propagating.

### IV. Priority-Driven Processing

Files MUST be classified by priority keywords: URGENT (immediate), REVIEW (current session), FYI (when queue clears). Default priority is Medium. Processing order MUST respect priority: URGENT first, then REVIEW, then FYI, then Medium. Priority is determined by keyword presence in filename or content.

### V. Security by Default

No secrets, tokens, or credentials stored in vault or committed to git. All configuration MUST use environment variables via `.env`. The vault is git-tracked — assume all vault contents are public. Sensitive files MUST NOT be placed in Inbox. `.claude/settings.local.json` is gitignored to prevent credential leakage.

### VI. Simplicity

Start with the minimum viable implementation. No premature abstractions — three similar lines are better than a premature helper. YAGNI: do not build for hypothetical future requirements. Every file and function MUST have a clear, single purpose. Prefer flat structures over deep nesting.

## Operational Standards

- Python 3.13+ required
- UTF-8 encoding everywhere, no exceptions
- ISO 8601 for all timestamps (`YYYY-MM-DDTHH:MM:SSZ`)
- Dashboard MUST be updated after every vault modification
- Action files use naming convention: `FILE_[original_name].md`
- One log file per day, append-only

## Development Workflow

- All changes go through git with descriptive commit messages
- SpecKit Plus slash commands used for spec-driven development
- Code review via pull requests when collaborating
- E2E test (`python scripts/e2e_test.py`) MUST pass before any release
- No force pushes to main/master branch

## Governance

This constitution is the authoritative guide for all development and operational decisions on the Shery Personal AI Employee project. Amendments require:
1. Documentation of the change and rationale
2. Version bump following semantic versioning (MAJOR.MINOR.PATCH)
3. Update to all dependent artifacts (CLAUDE.md, templates, README)
4. All PRs and code reviews MUST verify compliance with these principles

**Version**: 1.0.0 | **Ratified**: 2026-02-24 | **Last Amended**: 2026-02-24
