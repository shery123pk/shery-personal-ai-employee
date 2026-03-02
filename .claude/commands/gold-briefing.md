Generate a daily intelligence briefing using the Gold tier AI agents.

## Steps

1. Run `scripts/briefing_generator.py` to generate the daily briefing
2. The briefing includes: Executive Summary, Task Queue Status, Priorities, System Health
3. Output is saved to `AI_Employee_Vault/Briefings/gold_briefing_YYYY-MM-DD.md`
4. Display the briefing contents to the user
5. Update Dashboard.md with the latest briefing link

Uses the OrchestratorAgent for LLM-powered analysis when OpenAI API is configured.
Falls back to static data summary when in DEV_MODE.
