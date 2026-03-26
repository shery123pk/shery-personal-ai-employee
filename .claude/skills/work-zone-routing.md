---
name: work-zone-routing
description: Cloud/Local domain ownership and task routing
priority: high
tier: platinum
---

# Skill: Work-Zone Routing

Routes tasks to the correct zone based on domain ownership. Cloud handles read-only and draft operations; Local handles approval-gated and sensitive operations.

## Capabilities

### Domain classification
Classify actions into Cloud domains (email_triage, email_draft, social_draft, social_schedule, research, briefing) or Local domains (approval, send_email, post_social, payments, banking, dashboard).

### Zone-aware orchestration
The orchestrator checks zone ownership before processing. Tasks outside the current zone are delegated via Pending_Approval.

### Cloud agent
CloudAgent handles Cloud-zone tasks — triages emails, drafts social posts, generates research. All outputs require Local approval.

## Usage Examples

- "Route this email task to the correct zone"
- "Check if Cloud can handle social drafting"
- "Delegate this payment task to Local"
- "Switch to cloud work zone"

## Implementation

- Router: `scripts/work_zone.py` → `WorkZoneRouter`
- Cloud agent: `scripts/agents/cloud_agent.py` → `CloudAgent(BaseAgent)`
- Config: `WORK_ZONE` env var ("cloud" or "local")

## Rules
- Cloud CANNOT send emails, post to social media, or make payments
- All Cloud outputs go to Pending_Approval/<domain>/ for Local approval
- WORK_ZONE must be set explicitly ("cloud" or "local")
