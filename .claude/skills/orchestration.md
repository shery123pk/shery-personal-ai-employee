---
name: orchestration
description: Autonomous agent coordination and task execution loop
priority: critical
tier: gold
---

# Skill: Orchestration

The OrchestratorAgent coordinates all AI agents and runs the autonomous task execution loop.

## Capabilities

### Autonomous task loop
Scan Needs_Action/, prioritise tasks, route to the appropriate agent, execute with retry, and archive completed items to Done/.

### Intelligent task routing
Classify tasks (email/research/meeting/general) and route to the correct specialised agent.

### Daily intelligence briefing
Generate morning briefings with task queue status, priorities, and system health.

### Weekly CEO briefing
Generate strategic weekly summaries with achievements, pending items, and recommendations.

## Usage Examples

- "Run the autonomous loop to process all pending tasks"
- "Generate today's intelligence briefing"
- "Create the weekly CEO briefing"
- "Route this task to the right agent"

## Implementation

Uses `scripts/agents/orchestrator.py` → `OrchestratorAgent`.
Briefings saved to `AI_Employee_Vault/Briefings/`.

## Rules
- Respect AUTONOMOUS_MAX_ITERATIONS limit
- Always retry failed tasks up to AUTONOMOUS_RETRY_LIMIT
- Log all routing and execution results
- Write CURRENT_TASK.md during processing
