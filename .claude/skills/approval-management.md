---
name: approval-management
description: Manage human-in-the-loop approval workflow for sensitive actions
priority: critical
tier: silver
---

# Skill: Approval Management

Manage the approval workflow for sensitive actions that require human authorization.

## Capabilities

### Create approval requests
Route sensitive actions through the approval pipeline:
1. Generate approval request file in `AI_Employee_Vault/Pending_Approval/`
2. Include action type, summary, and all relevant details
3. Log the request to vault logs

Sensitive actions requiring approval:
- **send_email** — Sending emails via Gmail
- **post_linkedin** — Publishing posts to LinkedIn
- **delete** — Deleting any vault content
- **modify_config** — Changing system configuration

### Review pending approvals
List all files in `Pending_Approval/` showing:
- Action type and summary
- When the request was created
- Action details and data

### Process approval decisions
The approval watcher monitors `Approved/` and `Rejected/` folders:
- **Approved**: Executes the action, moves to `Done/`, logs success
- **Rejected**: Logs rejection, moves to `Done/` with status=rejected

### View approval history
Read completed approval files in `Done/` to show:
- What was approved/rejected
- When the decision was made
- Execution results

## Usage Examples

- "Create an approval request to send an email"
- "What approvals are pending?"
- "Show me the approval history for today"
- "How many actions were rejected this week?"

## Rules

- ALL sensitive actions MUST go through approval — never bypass
- Never auto-approve — always require human decision
- Log every approval request, decision, and execution
- Include full action details so the human can make an informed decision
- Update Dashboard.md after approval processing
