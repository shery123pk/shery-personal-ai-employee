---
name: email-intelligence
description: AI-powered email sentiment analysis and auto-response drafts
priority: high
tier: gold
---

# Skill: Email Intelligence

Analyse emails using the EmailAgent (LLM-powered) for sentiment, priority, and auto-response drafting.

## Capabilities

### Analyse email sentiment
Run the EmailAgent on email action items to classify sentiment as positive, negative, neutral, or urgent.

### Suggest email priority
The agent returns a priority recommendation (URGENT / REVIEW / FYI) based on email content analysis.

### Draft auto-responses
Generate context-aware professional reply drafts for emails using LLM reasoning.

### Batch email triage
Process multiple emails in Needs_Action/ through the EmailAgent for bulk triage.

## Usage Examples

- "Analyse the sentiment of the latest email in Needs_Action"
- "Draft a reply to the budget email"
- "Triage all email action items"

## Implementation

Uses `scripts/agents/email_agent.py` → `EmailAgent.execute()`.
Requires OpenAI API key or DEV_MODE=true for synthetic responses.

## Rules
- Never send emails without approval — only draft and suggest
- Log all analysis results to vault
- Respect DEV_MODE for cost-free testing
