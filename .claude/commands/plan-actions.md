# /plan-actions — Create execution plan from Needs_Action queue

Analyze all pending items in `AI_Employee_Vault/Needs_Action/` and create a structured Plan.md.

## Instructions

1. **Scan Needs_Action/**: Read all files in `AI_Employee_Vault/Needs_Action/` and parse their metadata (type, priority, source, status).

2. **Sort by priority**: Order items as URGENT → REVIEW → FYI → Medium.

3. **Analyze and group**: Identify related items, dependencies, and which actions are sensitive (require approval).

4. **Create Plan.md**: Write a structured plan to `AI_Employee_Vault/Plans/` using this format:

```markdown
# Plan: [Descriptive Title]

- **created_at:** [ISO 8601 timestamp]
- **source_items:** [comma-separated list of action files]
- **priority:** [highest priority from source items]
- **requires_approval:** [true if any step is sensitive]
- **estimated_steps:** [number of steps]

## Analysis

[What needs to be done and why, based on the action items]

## Steps

1. **[Step Title]** — owner: [agent/human], depends_on: [none/step N]
   - What to do
   - Expected outcome

## Approval Requirements

[Which steps need human approval and why, or "None" if all safe]

## Risks

- [Top risks and mitigations, max 3]
```

5. **Route approval if needed**: If any step involves sending email, posting to LinkedIn, or deleting content — create an approval request in `Pending_Approval/` referencing the plan.

6. **Log and update**: Log plan creation to `Logs/YYYY-MM-DD.json` and update `Dashboard.md`.

7. **Report**: Show the user the plan summary and path.

## Example output

```
Plan created: AI_Employee_Vault/Plans/Plan_2026-02-28T10-00-00+00-00.md
- 3 source items (1 URGENT, 1 REVIEW, 1 FYI)
- 5 steps planned
- Approval required: Yes (1 email action)
```
