---
name: task-optimization
description: AI-powered Eisenhower Matrix prioritisation and workload balancing
priority: high
tier: gold
---

# Skill: Task Optimization

Use the TaskOptimizer agent for intelligent task prioritisation via the Eisenhower Matrix.

## Capabilities

### Eisenhower Matrix classification
Classify tasks into four quadrants: DO_FIRST, SCHEDULE, DELEGATE, ELIMINATE using LLM reasoning.

### Priority matrix report
Generate a markdown report showing all tasks categorised by quadrant with urgency/importance scores.

### Workload balancing
Recommend task redistribution based on urgency and importance analysis.

## Usage Examples

- "Prioritise all tasks in Needs_Action using Eisenhower Matrix"
- "What should I focus on today?"
- "Generate a priority report"

## Implementation

Uses `scripts/agents/task_optimizer.py` → `TaskOptimizer.execute()`.
Report saved to `AI_Employee_Vault/Plans/eisenhower_matrix_*.md`.

## Rules
- Always scan the full Needs_Action/ queue
- Save reports to Plans/ with date stamps
- Log optimisation results to vault
