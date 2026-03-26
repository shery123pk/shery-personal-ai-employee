---
name: vault-sync
description: Git-based vault synchronisation between Cloud and Local zones
priority: high
tier: platinum
---

# Skill: Vault Sync

Git-based synchronisation keeps the Obsidian vault consistent between Cloud and Local zones.

## Capabilities

### Full sync cycle
Pull remote changes, commit local changes, and push — in a single `sync()` call.

### Conflict resolution
Dashboard.md prefers Local (ours); all other files prefer Cloud (theirs).

### Periodic sync
SyncWatcher (BaseWatcher) runs sync at a configurable interval.

### DEV_MODE support
In DEV_MODE, logs actions but skips actual git commands.

## Usage Examples

- "Sync the vault with the remote repository"
- "Check vault sync status"
- "Start the sync watcher"
- "Resolve vault conflicts"

## Implementation

- Module: `scripts/vault_sync.py` → `VaultSync`
- Watcher: `scripts/sync_watcher.py` → `SyncWatcher(BaseWatcher)`
- Config: `VAULT_SYNC_BRANCH`, `VAULT_SYNC_INTERVAL_SEC`

## Rules
- Dashboard.md conflicts always resolved in favour of Local
- Sync interval configurable via VAULT_SYNC_INTERVAL_SEC
- DEV_MODE skips git operations
