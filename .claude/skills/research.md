---
name: research
description: AI-powered deep research with summarisation
priority: medium
tier: gold
---

# Skill: Research

Run the ResearchAgent for multi-source research with LLM summarisation.

## Capabilities

### Deep research on a topic
Given a topic or question, generate a comprehensive research summary with key findings, detailed analysis, and recommendations.

### Content summarisation
Summarise arbitrary content (articles, documents, reports) into concise summaries.

### Knowledge base building
Save research outputs to `Knowledge_Base/` for future reference.

## Usage Examples

- "Research the latest trends in AI agent architectures"
- "Summarise this document"
- "Build a knowledge base entry on Python async patterns"

## Implementation

Uses `scripts/agents/research_agent.py` → `ResearchAgent.execute()`.
Output saved to `AI_Employee_Vault/Knowledge_Base/`.

## Rules
- Save all research summaries to Knowledge_Base/
- Include generation timestamps in output
- Respect token limits for cost efficiency
