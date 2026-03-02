Run the TaskOptimizer agent to generate an Eisenhower Matrix for all pending tasks.

## Steps

1. Initialise the TaskOptimizer from `scripts/agents/task_optimizer.py`
2. Scan all tasks in `AI_Employee_Vault/Needs_Action/`
3. Classify each task into Eisenhower quadrants (DO_FIRST, SCHEDULE, DELEGATE, ELIMINATE)
4. Generate a priority matrix report
5. Save the report to `AI_Employee_Vault/Plans/eisenhower_matrix_<date>.md`
6. Display the prioritised task list to the user

Uses LLM classification when OpenAI API is configured. Falls back to heuristic classification in DEV_MODE.
