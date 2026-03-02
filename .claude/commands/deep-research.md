Run the ResearchAgent for deep research on a topic.

Provide a topic as the argument: `/deep-research <topic>`

## Steps

1. Initialise the ResearchAgent from `scripts/agents/research_agent.py`
2. Execute research with the given topic
3. Save the research summary to `AI_Employee_Vault/Knowledge_Base/research_<topic>_<date>.md`
4. Display key findings and summary to the user
5. Log the research action to the vault

## Example

```
/deep-research AI agent orchestration patterns
```

Uses LLM for analysis when OpenAI API is configured. Falls back to synthetic responses in DEV_MODE.
