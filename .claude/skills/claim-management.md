---
name: claim-management
description: Claim-by-move concurrency for multi-agent task processing
priority: high
tier: platinum
---

# Skill: Claim Management

Atomic claim-by-move concurrency prevents multiple agents from processing the same task.

## Capabilities

### Atomic claiming
`os.rename()` atomically moves a file from Needs_Action/ to In_Progress/<agent>/ — if two agents race, only one wins.

### Release to Done
Move completed claims from In_Progress/<agent>/ to Done/.

### Release to Approval
Move claims requiring approval to Pending_Approval/<domain>/.

### Stale claim cleanup
Return claims older than `max_age_seconds` back to Needs_Action/ for reprocessing.

## Usage Examples

- "Claim a task for the email agent"
- "Release the completed task to Done"
- "Clean up stale claims older than 1 hour"
- "Check In_Progress for stuck tasks"

## Implementation

- Module: `scripts/claim_manager.py` → `ClaimManager(agent_name)`
- Per-agent dirs: `AI_Employee_Vault/In_Progress/<agent>/`
- Integrated into OrchestratorAgent's autonomous loop

## Rules
- Claims are atomic — race conditions are handled by OS-level rename
- Stale claims (default: 1 hour) are automatically returned
- Works identically in DEV_MODE (pure file ops)
