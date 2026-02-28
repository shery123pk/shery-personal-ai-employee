---
name: linkedin-posting
description: Generate and post professional content to LinkedIn with approval workflow
priority: required
tier: silver
---

# Skill: LinkedIn Posting

Generate professional LinkedIn content and post it through the approval workflow.

## Capabilities

### Generate LinkedIn post content
Create professional business content for LinkedIn:
- Adapt tone to professional/business audience
- Include relevant hashtags
- Keep posts concise and engaging (under 1300 characters)
- Support different formats: updates, announcements, thought leadership

### Create LinkedIn post request
Use `scripts/linkedin_poster.py` to create an approval request:
1. Generate the post content
2. Call `create_linkedin_post_request(content)` to route through approval
3. File appears in `Pending_Approval/` for human review

### Publish approved posts
After human moves file to `Approved/`:
- Approval watcher detects the file
- Calls `publish_to_linkedin()` with the content
- Supports dry-run mode when `LINKEDIN_DRY_RUN=true` in .env
- Logs result to vault

### View posting history
Read `Done/` folder for completed LinkedIn post approvals showing:
- Post content
- Whether it was approved or rejected
- Publication result (success, dry-run, or error)

## Usage Examples

- "Draft a LinkedIn post about our Q1 achievements"
- "Create a LinkedIn announcement for our new product launch"
- "Generate a thought leadership post about AI in business"
- "What LinkedIn posts have been published this week?"

## Rules

- ALL posts MUST go through approval — never publish directly
- Keep posts professional and brand-appropriate
- Include 3-5 relevant hashtags
- Respect LinkedIn's character limits
- Log all post attempts (success, dry-run, failure)
- If LINKEDIN_DRY_RUN=true, log instead of posting (default safe mode)
