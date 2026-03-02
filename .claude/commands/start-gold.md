Launch the full Gold tier AI Employee orchestrator.

Start all 5 watchers, the scheduler with 7 jobs, and initialise all 5 AI agents.

## Steps

1. Verify vault structure (all folders exist: Inbox, Needs_Action, Done, Plans, Pending_Approval, Approved, Rejected, Logs, Briefings, Knowledge_Base, Finance)
2. Start the FileSystemWatcher on Inbox/
3. Start the GmailWatcher (if credentials configured)
4. Start the ApprovalWatcher on Approved/ and Rejected/
5. Start the ProcessWatchdog for system health monitoring
6. Start the FinanceWatcher on Finance/
7. Initialise the OrchestratorAgent with all 5 AI agents
8. Start the scheduler with all 7 periodic jobs
9. Generate an initial daily briefing
10. Update Dashboard.md with Gold tier status

Report the system status when all components are running.
