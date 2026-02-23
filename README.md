# Bronze Tier AI Employee

> **GIAIC / Panaversity Personal AI Employee Hackathon 0**
> **Owner:** Sharmeen Asif (@shery123pk)

A Bronze Tier Personal AI Employee that uses Claude Code as the AI agent, an Obsidian-compatible vault for task management, and a Python file-system watcher for automated file intake.

## Architecture

```
┌─────────────────────────────────────────┐
│            Claude Code (Agent)          │
│  Skills: vault · watcher · processing   │
└────────────┬───────────────┬────────────┘
             │               │
     ┌───────▼───────┐ ┌────▼──────────┐
     │  File Watcher  │ │ Obsidian Vault │
     │  (watchdog)    │ │               │
     └───────┬───────┘ │  Inbox/       │
             │          │  Needs_Action/ │
             └─────────►│  Done/        │
                        │  Logs/        │
                        └───────────────┘
```

**Data Flow:** Drop a file in `Inbox/` → Watcher detects it → Creates action in `Needs_Action/` → Claude processes → Moves to `Done/` → Logs to `Logs/` → Updates `Dashboard.md`

## Setup

### Prerequisites

- Python 3.13+
- Claude Code CLI
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/shery123pk/fte_zero.git
cd fte_zero

# Install Python dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

### SpecKit Plus (already initialized)

The project includes SpecKit Plus for spec-driven development. Slash commands available:

- `/sp.constitution` — View/edit project principles
- `/sp.specify` — Create feature specifications
- `/sp.plan` — Create implementation plans
- `/sp.tasks` — Generate tasks from plans

## Usage

### Start the File Watcher

```bash
python scripts/file_watcher.py
```

The watcher monitors `AI_Employee_Vault/Inbox/` and creates action files in `Needs_Action/` when new files appear.

### Drop a File

Place any file in `AI_Employee_Vault/Inbox/`. The watcher will:

1. Detect the file
2. Parse priority from filename (URGENT, REVIEW, FYI)
3. Create `FILE_[name].md` in `Needs_Action/`
4. Log the event to `Logs/YYYY-MM-DD.json`

### Process with Claude

Use Claude Code to process action items:

```
> Process all items in Needs_Action
```

Claude will use the **file-processing** skill to handle each item, move completed work to `Done/`, and update the Dashboard.

## Agent Skills

| Skill | Purpose |
|-------|---------|
| `vault-management` | Read/write/move vault files, update Dashboard |
| `watcher-management` | Start/stop watcher, check status, view logs |
| `file-processing` | Process Needs_Action items, archive to Done |

## Project Structure

```
fte_zero/
├── .claude/
│   ├── commands/          ← SpecKit Plus /sp.* commands
│   └── skills/            ← 3 Agent Skills
├── .specify/              ← SpecKit Plus templates & scripts
├── AI_Employee_Vault/     ← Obsidian Vault
│   ├── Inbox/             ← Drop files here
│   ├── Needs_Action/      ← Pending action items
│   ├── Done/              ← Completed archive
│   ├── Logs/              ← Daily JSON logs
│   ├── Dashboard.md       ← Status overview
│   └── Company_Handbook.md
├── scripts/
│   ├── file_watcher.py    ← Watchdog-based watcher
│   └── logger.py          ← Structured logging
├── .env.example
├── .gitignore
├── CLAUDE.md
├── README.md
└── requirements.txt
```

## License

Built for the GIAIC / Panaversity Personal AI Employee Hackathon 0.
