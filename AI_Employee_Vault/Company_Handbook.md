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
2. **Needs_Action** — Action items created by the watcher. Each file contains metadata about the original file and required action.
3. **Done** — Archive of completed items. Files are moved here after processing with a completion timestamp appended.
4. **Logs** — Daily JSON log files named `YYYY-MM-DD.json`. Each entry records timestamp, action, source file, and result.

## File Retention Rules

- **Inbox**: Files are moved or referenced within seconds of detection. Originals remain in Inbox for reference.
- **Needs_Action**: Items should be processed within the current session. Stale items (>24h) should be flagged.
- **Done**: Retained indefinitely for audit trail.
- **Logs**: Retained indefinitely. One file per day.

## Processing Rules

1. When a file arrives in Inbox, the watcher creates a corresponding action file in Needs_Action.
2. Action files use the naming convention: `FILE_[original_name].md`
3. Each action file contains:
   - Original filename
   - Detection timestamp (ISO 8601)
   - File size
   - Priority (parsed from filename/content)
   - Status: `pending`
4. When processed, the action file is moved to Done with status updated to `completed`.

## Security Policies

- No secrets, tokens, or credentials stored in the vault.
- Environment variables used for all configuration (see `.env.example`).
- Vault contents are committed to git — do not place sensitive files in Inbox.
