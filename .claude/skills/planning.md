---
name: planning
description: Analyze Needs_Action items and create structured Plans with reasoning
priority: required
tier: silver
---

# Skill: Planning (Claude Reasoning Loop)

Analyze pending action items and create structured execution plans.

## Capabilities

### Analyze Needs_Action queue
Read all items in `AI_Employee_Vault/Needs_Action/` and:
1. Parse metadata (type, priority, source, details)
2. Group related items
3. Identify dependencies between actions
4. Sort by priority: URGENT → REVIEW → FYI → Medium

### Create Plan.md files
Generate structured plans in `AI_Employee_Vault/Plans/`:

```markdown
# Plan: [Title]

- **created_at:** [ISO 8601 timestamp]
- **source_items:** [list of Needs_Action files analyzed]
- **priority:** [highest priority from source items]
- **requires_approval:** [true/false — true if any step is sensitive]
- **estimated_steps:** [number]

## Analysis

[Summary of what needs to be done and why]

## Steps

1. **[Step Title]** — owner: [agent/human], depends_on: [none/step N]
   - Description of what to do
   - Expected outcome

2. ...

## Approval Requirements

[List any steps that require human approval and why]

## Risks

- [Risk 1 and mitigation]
- [Risk 2 and mitigation]
```

### Route sensitive plans through approval
If any step involves a sensitive action (sending email, posting to LinkedIn, deleting content):
1. Create the Plan.md in `Plans/`
2. Create an approval request in `Pending_Approval/` referencing the plan
3. Only execute after human approval

### Process items by priority
Always process in priority order:
1. URGENT items first
2. REVIEW items next
3. FYI items last
4. Medium (default) items last

## Usage Examples

- "Plan how to handle all items in Needs_Action"
- "Create a plan for the urgent email from the CFO"
- "What's the execution plan for today's action items?"
- "Show me all plans created this week"

## Rules

- Always read ALL Needs_Action items before planning
- Plans MUST include concrete, actionable steps
- Sensitive actions MUST be flagged for approval
- Log plan creation to vault logs
- Update Dashboard.md after creating plans
- Never execute sensitive steps without approval
