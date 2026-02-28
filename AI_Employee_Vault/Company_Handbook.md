# Company Handbook — AI Employee Operations

## Priority Keywords

Files and tasks are prioritized by keywords found in their name or content:

| Keyword | Priority | Response Time |
|---------|----------|---------------|
| URGENT | High | Process immediately |
| REVIEW | Medium | Process within current session |
| FYI | Low | Process when queue is clear |

Files without priority keywords default to **Medium** priority.

## File Organization Policies

1. **Inbox** — Drop zone for new files. The watcher monitors this folder continuously.
2. **Needs_Action** — Action items created by watchers (file system, Gmail). Each file contains metadata about the source and required action.
3. **Done** — Archive of completed items. Files are moved here after processing with a completion timestamp appended.
4. **Logs** — Daily JSON log files named `YYYY-MM-DD.json`. Each entry records timestamp, action, source file, and result.
5. **Plans** — Structured execution plans created by the planning skill. Each plan references source action items and includes steps, dependencies, and risks.
6. **Pending_Approval** — Approval requests for sensitive actions awaiting human review.
7. **Approved** — Files moved here by humans to authorize an action.
8. **Rejected** — Files moved here by humans to deny an action.

## File Retention Rules

- **Inbox**: Files are moved or referenced within seconds of detection. Originals remain in Inbox for reference.
- **Needs_Action**: Items should be processed within the current session. Stale items (>24h) should be flagged.
- **Done**: Retained indefinitely for audit trail.
- **Logs**: Retained indefinitely. One file per day.
- **Plans**: Retained indefinitely for reference.
- **Pending_Approval**: Should be reviewed within 24 hours.

## Processing Rules

1. When a file arrives in Inbox, the watcher creates a corresponding action file in Needs_Action.
2. Action files use the naming convention: `FILE_[original_name].md`
3. Email actions use: `EMAIL_[subject_slug].md`
4. Each action file contains:
   - Source type (file/email)
   - Detection timestamp (ISO 8601)
   - Priority (parsed from filename/labels)
   - Status: `pending`
5. When processed, the action file is moved to Done with status updated to `completed`.

## Approval Workflow (Human-in-the-Loop)

**Sensitive actions** require human approval before execution:

| Action | Why Approval Required |
|--------|----------------------|
| Send email | Prevents unauthorized communication |
| Post to LinkedIn | Prevents unreviewed public posts |
| Delete content | Prevents accidental data loss |
| Modify config | Prevents system misconfiguration |

**Workflow:**
1. Agent creates an approval request in `Pending_Approval/`
2. Human reviews the request details
3. Human moves file to `Approved/` (execute) or `Rejected/` (deny)
4. Approval watcher detects and acts accordingly
5. Result is logged and file is archived to `Done/`

## Email Policies

- Gmail is checked every 5 minutes by the scheduler
- Starred emails are treated as URGENT priority
- Important-labeled emails are REVIEW priority
- All other emails are FYI priority
- Sending emails always requires approval
- Creating drafts is safe (no approval needed)

## LinkedIn Policies

- All LinkedIn posts must go through approval workflow
- Posts should be professional and brand-appropriate
- Dry-run mode is enabled by default for safety
- Include relevant hashtags (3-5 per post)

## Scheduling Policies

- Gmail polling: every 5 minutes (configurable)
- Queue processing: every 10 minutes (configurable)
- Approval checking: every 5 minutes (configurable)
- Daily briefing: 9:00 AM (configurable)

## Security Policies

- No secrets, tokens, or credentials stored in the vault.
- Environment variables used for all configuration (see `.env.example`).
- Vault contents are committed to git — do not place sensitive files in Inbox.
- OAuth tokens (`token.json`, `credentials.json`) are gitignored.
- All external actions (email, LinkedIn) require human approval.
