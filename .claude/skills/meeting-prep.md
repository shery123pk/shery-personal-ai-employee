---
name: meeting-prep
description: AI-powered meeting preparation and follow-up documentation
priority: medium
tier: gold
---

# Skill: Meeting Preparation

Use the MeetingAgent for structured meeting agendas and follow-up action items.

## Capabilities

### Prepare meeting agendas
Generate structured agendas with objectives, discussion points, time estimates, and next steps.

### Extract action items
Parse meeting notes and extract clear action items with owners, deadlines, and priorities.

### Meeting summaries
Generate concise meeting summaries from raw notes.

## Usage Examples

- "Prepare an agenda for the team standup tomorrow"
- "Extract action items from these meeting notes"
- "Summarise the client meeting discussion"

## Implementation

Uses `scripts/agents/meeting_agent.py` → `MeetingAgent.execute()`.

## Rules
- Always include owners and deadlines for action items
- Format output as markdown for Obsidian compatibility
- Log all meeting-related actions to vault
