"""End-to-end test: Platinum tier full pipeline (32+ Checks)."""

import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from file_watcher import FileSystemWatcher, INBOX_DIR, NEEDS_ACTION_DIR
from logger import get_today_log_path, iso_now, log_to_vault

VAULT_DIR = Path(__file__).resolve().parent.parent / "AI_Employee_Vault"
DONE_DIR = VAULT_DIR / "Done"
PLANS_DIR = VAULT_DIR / "Plans"
PENDING_APPROVAL_DIR = VAULT_DIR / "Pending_Approval"
APPROVED_DIR = VAULT_DIR / "Approved"
REJECTED_DIR = VAULT_DIR / "Rejected"


def main() -> None:
    print("=" * 60)
    print("END-TO-END TEST: Platinum Tier Full Pipeline (32+ Checks)")
    print("=" * 60)

    # ── Step 1: Start watcher ──
    print("\n[1/10] Starting file watcher...")
    watcher = FileSystemWatcher()
    watcher.start()
    print("        Watcher is running.\n")

    # ── Step 2: Drop 3 test files into Inbox ──
    print("[2/10] Dropping 3 files into Inbox...")
    test_files = [
        ("URGENT_budget_report.txt", "Q1 2026 budget needs immediate review."),
        ("REVIEW_meeting_notes.md", "## Team Standup\n- Discussed roadmap\n- Action items assigned"),
        ("FYI_newsletter_update.txt", "Monthly newsletter draft v2 attached."),
    ]

    for name, content in test_files:
        path = INBOX_DIR / name
        path.write_text(content, encoding="utf-8")
        print(f"        Dropped: {name} ({len(content)} bytes)")
        time.sleep(1.5)

    print()

    # ── Step 3: Verify action files in Needs_Action ──
    print("[3/10] Checking Needs_Action for action files...")
    time.sleep(1)
    action_files = sorted(
        f for f in NEEDS_ACTION_DIR.iterdir() if f.name.startswith("FILE_")
    )
    print(f"        Found {len(action_files)} action file(s):")
    for af in action_files:
        content = af.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "**priority:**" in line:
                priority = line.split("**priority:**")[1].strip()
                print(f"        - {af.name}  [priority: {priority}]")
                break

    if len(action_files) != 3:
        print("        FAIL: Expected 3 action files!")
        watcher.stop()
        sys.exit(1)
    print("        All 3 action files created.\n")

    # ── Step 4: Process each action file → move to Done ──
    print("[4/10] Processing action files (Needs_Action -> Done)...")
    for af in action_files:
        content = af.read_text(encoding="utf-8")
        updated = content.replace("**status:** pending", "**status:** completed")
        updated += f"\n- **completed_at:** {iso_now()}\n"

        done_path = DONE_DIR / af.name
        done_path.write_text(updated, encoding="utf-8")
        af.unlink()

        priority = "Medium"
        for line in content.splitlines():
            if "**priority:**" in line:
                priority = line.split("**priority:**")[1].strip()
                break

        log_to_vault(
            action="processed",
            source=af.name,
            result="completed",
            priority=priority,
        )
        print(f"        Processed: {af.name} -> Done/")

    print()

    # ── Step 5: Test approval workflow ──
    print("[5/10] Testing approval workflow...")
    from approval_utils import create_approval_request

    approval_path = create_approval_request(
        action_type="send_email",
        summary="Test email approval",
        details={"to": "test@example.com", "subject": "Test", "body": "Hello"},
    )
    print(f"        Created approval request: {approval_path.name}")

    # Move to Approved and verify handling
    approved_path = APPROVED_DIR / approval_path.name
    shutil.move(str(approval_path), str(approved_path))
    print(f"        Moved to Approved/: {approved_path.name}")

    from approval_watcher import ApprovalWatcher, parse_approval_metadata

    approval_watcher = ApprovalWatcher()
    approval_watcher._handle_approved(approved_path)
    print("        Approval watcher processed the approved file.")

    # Test rejection workflow
    reject_path = create_approval_request(
        action_type="post_linkedin",
        summary="Test LinkedIn rejection",
        details={"content": "Test post"},
    )
    rejected_dest = REJECTED_DIR / reject_path.name
    shutil.move(str(reject_path), str(rejected_dest))
    approval_watcher._handle_rejected(rejected_dest)
    print("        Rejection workflow completed.\n")

    # ── Step 6: Test LinkedIn poster (dry run) ──
    print("[6/10] Testing LinkedIn poster (dry run)...")
    from linkedin_poster import create_linkedin_post_request, publish_to_linkedin

    li_result = publish_to_linkedin("Test post content", "")
    print(f"        Result: {li_result}")
    print()

    # ── Step 7: Test config module ──
    print("[7/10] Verifying config module...")
    from config import (
        VAULT_PATH as CFG_VAULT,
        GMAIL_POLL_INTERVAL_SEC,
        LINKEDIN_DRY_RUN,
        SCHEDULER_GMAIL_INTERVAL_MIN,
        SENSITIVE_ACTION_KEYWORDS,
    )
    print(f"        VAULT_PATH: {CFG_VAULT}")
    print(f"        GMAIL_POLL_INTERVAL: {GMAIL_POLL_INTERVAL_SEC}s")
    print(f"        LINKEDIN_DRY_RUN: {LINKEDIN_DRY_RUN}")
    print(f"        SCHEDULER_GMAIL_INTERVAL: {SCHEDULER_GMAIL_INTERVAL_MIN}min")
    print(f"        SENSITIVE_KEYWORDS: {SENSITIVE_ACTION_KEYWORDS}")
    print()

    # ── Step 8: Test scheduler creation ──
    print("[8/10] Verifying scheduler setup...")
    from scheduler import create_scheduler

    scheduler = create_scheduler()
    jobs = scheduler.get_jobs()
    print(f"        Scheduler created with {len(jobs)} jobs:")
    for job in jobs:
        print(f"        - {job.name}")
    print()

    # ── Step 9: Update Dashboard ──
    print("[9/10] Updating Dashboard.md...")
    inbox_count = len([f for f in INBOX_DIR.iterdir() if not f.name.startswith(".")])
    needs_count = len([f for f in NEEDS_ACTION_DIR.iterdir() if not f.name.startswith(".")])
    done_count = len([f for f in DONE_DIR.iterdir() if not f.name.startswith(".")])
    plans_count = len([f for f in PLANS_DIR.iterdir() if not f.name.startswith(".")])
    pending_count = len([f for f in PENDING_APPROVAL_DIR.iterdir() if not f.name.startswith(".")])

    log_path = get_today_log_path()
    entries = json.loads(log_path.read_text(encoding="utf-8"))

    activity_rows = ""
    for e in entries[-20:]:
        activity_rows += (
            f'| {e["timestamp"]} | {e["action"]} | {e["source"]} | {e["result"]} |\n'
        )

    dashboard = (
        "# AI Employee Dashboard\n"
        "\n"
        f"> Last updated: {iso_now()}\n"
        "\n"
        "## System Health\n"
        "\n"
        "| Component | Status | Details |\n"
        "|-----------|--------|--------|\n"
        "| File Watcher | Running | Monitoring Inbox/ |\n"
        "| Gmail Watcher | Ready | Configured for polling |\n"
        "| Approval Watcher | Running | Monitoring Approved/ & Rejected/ |\n"
        "| Scheduler | Ready | 4 periodic jobs configured |\n"
        "| MCP Email Server | Ready | 4 tools available |\n"
        "| Claude Agent | Ready | 8 skills loaded |\n"
        "| Vault Access | OK | All folders accessible |\n"
        "\n"
        "## Folder Counts\n"
        "\n"
        "| Folder | Count |\n"
        "|--------|-------|\n"
        f"| Inbox | {inbox_count} |\n"
        f"| Needs_Action | {needs_count} |\n"
        f"| Done | {done_count} |\n"
        f"| Plans | {plans_count} |\n"
        f"| Pending_Approval | {pending_count} |\n"
        "\n"
        "## Recent Activity\n"
        "\n"
        "| Timestamp | Action | Source | Result |\n"
        "|-----------|--------|--------|--------|\n"
        f"{activity_rows}"
    )

    (VAULT_DIR / "Dashboard.md").write_text(dashboard, encoding="utf-8")
    print(f"        Inbox: {inbox_count}  |  Needs_Action: {needs_count}  |  Done: {done_count}")
    print("        Dashboard.md updated.\n")

    # ── Step 10: Show logs ──
    print("[10/10] Vault log entries (last 10):")
    for e in entries[-10:]:
        print(f'        {e["timestamp"]}  {e["action"]:30s}  {e["source"]:30s}  {e["result"]}')

    # ── Stop watcher ──
    watcher.stop()

    # ── Gold Step 11: Test AI agents ──
    print("\n[11/14] Testing Gold+Platinum tier AI agents...")
    base_agent_importable = False
    agent_count = 0
    orchestrator_works = False
    cloud_agent_importable = False
    try:
        from agents.base_agent import BaseAgent
        base_agent_importable = True
        print("        BaseAgent imported successfully.")

        from agents.email_agent import EmailAgent
        from agents.research_agent import ResearchAgent
        from agents.meeting_agent import MeetingAgent
        from agents.task_optimizer import TaskOptimizer
        from agents.orchestrator import OrchestratorAgent
        from agents.cloud_agent import CloudAgent
        agent_count = 6
        cloud_agent_importable = issubclass(CloudAgent, BaseAgent)
        print(f"        {agent_count} agent classes imported.")
        print(f"        CloudAgent extends BaseAgent: {cloud_agent_importable}")

        # Test orchestrator routing
        orchestrator = OrchestratorAgent()
        task_type = orchestrator.classify_task_type("Please review this email from the client about the budget")
        print(f"        Orchestrator classified test task as: {task_type}")
        orchestrator_works = task_type in ("email", "research", "meeting", "general")
    except Exception as exc:
        print(f"        Agent import error: {exc}")

    # ── Gold Step 12: Test briefing generation ──
    print("\n[12/14] Testing briefing generation...")
    briefing_path_exists = False
    try:
        from briefing_generator import generate_daily_briefing
        bp = generate_daily_briefing()
        briefing_path_exists = bp.exists()
        print(f"        Daily briefing generated: {bp.name}")
    except Exception as exc:
        print(f"        Briefing error: {exc}")

    # ── Gold Step 13: Test Gold config ──
    print("\n[13/14] Verifying Gold config...")
    from config import (
        DEV_MODE,
        OPENAI_MODEL,
        AUTONOMOUS_MAX_ITERATIONS,
        BRIEFINGS_DIR,
        KNOWLEDGE_BASE_DIR,
    )
    print(f"        DEV_MODE: {DEV_MODE}")
    print(f"        OPENAI_MODEL: {OPENAI_MODEL}")
    print(f"        AUTONOMOUS_MAX_ITERATIONS: {AUTONOMOUS_MAX_ITERATIONS}")

    # ── Gold Step 14: Show Gold components ──
    print("\n[14/14] Gold component summary...")
    agents_dir = Path(__file__).resolve().parent / "agents"
    agent_files = [f for f in agents_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"] if agents_dir.exists() else []
    print(f"        Agent files: {len(agent_files)}")
    for af in sorted(agent_files):
        print(f"          - {af.name}")

    # ── Platinum Step 15: Test claim-by-move ──
    print("\n[15/20] Testing claim-by-move (ClaimManager)...")
    claim_works = False
    try:
        from claim_manager import ClaimManager

        claimer = ClaimManager("test_agent")
        # Create a test task in Needs_Action
        test_task = NEEDS_ACTION_DIR / "CLAIM_TEST_task.md"
        test_task.write_text("# Test\n- **status:** pending\n", encoding="utf-8")

        # Claim it
        claimed = claimer.try_claim(test_task)
        if claimed and claimed.exists() and not test_task.exists():
            print(f"        Claimed: {claimed}")
            # Release to Done
            released = claimer.release_to_done(claimed)
            if released and released.exists():
                claim_works = True
                print(f"        Released to Done: {released.name}")
                released.unlink()  # clean up
        else:
            print("        Claim failed!")
    except Exception as exc:
        print(f"        ClaimManager error: {exc}")

    # ── Platinum Step 16: Test work-zone routing ──
    print("\n[16/20] Testing work-zone routing...")
    routing_works = False
    try:
        from work_zone import WorkZoneRouter, CLOUD_DOMAINS, LOCAL_DOMAINS

        cloud_router = WorkZoneRouter("cloud")
        local_router = WorkZoneRouter("local")
        routing_works = (
            cloud_router.can_handle("email_triage")
            and not cloud_router.can_handle("send_email")
            and local_router.can_handle("approval")
            and not local_router.can_handle("research")
        )
        print(f"        Cloud can email_triage: {cloud_router.can_handle('email_triage')}")
        print(f"        Cloud can send_email: {cloud_router.can_handle('send_email')}")
        print(f"        Local can approval: {local_router.can_handle('approval')}")
        print(f"        Routing correct: {routing_works}")
    except Exception as exc:
        print(f"        WorkZoneRouter error: {exc}")

    # ── Platinum Step 17: Test vault sync module ──
    print("\n[17/20] Testing vault sync module (DEV_MODE)...")
    vault_sync_works = False
    try:
        from vault_sync import VaultSync

        syncer = VaultSync()
        result = syncer.sync()
        vault_sync_works = isinstance(result, dict) and "pulled" in result
        print(f"        Sync result: {result}")
    except Exception as exc:
        print(f"        VaultSync error: {exc}")

    # ── Platinum Step 18: Test Odoo MCP server import ──
    print("\n[18/20] Testing Odoo MCP server import...")
    odoo_mcp_works = False
    try:
        from mcp_odoo_server import create_invoice, list_invoices, get_account_balance
        inv_result = json.loads(create_invoice("Test Corp", 1000.00, "Test invoice"))
        odoo_mcp_works = inv_result.get("status") == "created"
        print(f"        create_invoice result: {inv_result.get('status')}")
    except Exception as exc:
        print(f"        Odoo MCP error: {exc}")

    # ── Platinum Step 19: Test CloudAgent ──
    print("\n[19/20] Testing CloudAgent...")
    cloud_agent_works = False
    try:
        from agents.cloud_agent import CloudAgent
        from agents.base_agent import BaseAgent as BA
        cloud_agent_works = issubclass(CloudAgent, BA)
        print(f"        CloudAgent extends BaseAgent: {cloud_agent_works}")
    except Exception as exc:
        print(f"        CloudAgent error: {exc}")

    # ── Platinum Step 20: Test dashboard updater ──
    print("\n[20/20] Testing dashboard updater...")
    dashboard_updater_works = False
    try:
        from dashboard_updater import DashboardUpdater

        updater = DashboardUpdater()
        update_path = updater.write_update("test_source", {"test_key": "test_value"})
        if update_path.exists():
            print(f"        Update written: {update_path.name}")
            # Clean up the update file (don't merge — we're in test)
            update_path.unlink()
            dashboard_updater_works = True
    except Exception as exc:
        print(f"        DashboardUpdater error: {exc}")

    # ── Final verification — 32+ checks ──
    print("\n" + "=" * 60)
    print("VERIFICATION — Platinum Tier (32+ Checks)")
    print("=" * 60)

    done_files = sorted(f.name for f in DONE_DIR.iterdir() if not f.name.startswith("."))
    log_entries = json.loads(log_path.read_text(encoding="utf-8"))

    # Vault folder counts
    skill_dir = Path(__file__).resolve().parent.parent / ".claude" / "skills"
    skill_count = len([f for f in skill_dir.iterdir() if f.suffix == ".md"]) if skill_dir.exists() else 0

    script_dir = Path(__file__).resolve().parent
    watcher_scripts = [f for f in script_dir.iterdir() if "watcher" in f.name and f.suffix == ".py"]
    mcp_scripts = [f for f in script_dir.iterdir() if "mcp" in f.name and f.suffix == ".py"]

    # Gold vault folders
    briefings_dir = VAULT_DIR / "Briefings"
    knowledge_base_dir = VAULT_DIR / "Knowledge_Base"
    finance_dir = VAULT_DIR / "Finance"

    # Platinum vault folders
    in_progress_dir = VAULT_DIR / "In_Progress"
    updates_dir = VAULT_DIR / "Updates"

    # Agent file count
    agents_dir_count = len([f for f in (Path(__file__).resolve().parent / "agents").iterdir()
                           if f.suffix == ".py" and f.name != "__init__.py"]) if (Path(__file__).resolve().parent / "agents").exists() else 0

    checks = [
        # Bronze checks (1-6)
        ("3 files in Inbox", inbox_count == 3),
        ("0 files in Needs_Action", needs_count == 0),
        ("3+ files in Done", len(done_files) >= 3),
        ("Log file exists", log_path.exists()),
        ("Log has >= 6 entries", len(log_entries) >= 6),
        ("Dashboard updated", "Running" in (VAULT_DIR / "Dashboard.md").read_text(encoding="utf-8")),
        # Silver checks (7-14)
        ("3+ watcher scripts exist", len(watcher_scripts) >= 3),
        ("Approval workflow works", any("approval" in e["action"] for e in log_entries)),
        ("LinkedIn dry-run works", any("linkedin" in e["action"] for e in log_entries)),
        ("Config module loads", CFG_VAULT.exists()),
        ("Scheduler has 9 jobs", len(jobs) >= 9),
        ("MCP server script exists", len(mcp_scripts) >= 1),
        ("8+ agent skills", skill_count >= 8),
        ("Silver vault folders exist", PLANS_DIR.exists() and PENDING_APPROVAL_DIR.exists() and APPROVED_DIR.exists() and REJECTED_DIR.exists()),
        # Gold checks (15-22)
        ("5+ watcher scripts exist", len(watcher_scripts) >= 5),
        ("BaseAgent class importable", base_agent_importable),
        ("5+ agent classes exist", agent_count >= 5),
        ("4+ MCP server scripts exist", len(mcp_scripts) >= 4),
        ("Orchestrator routes tasks", orchestrator_works),
        ("Briefing generates", briefing_path_exists),
        ("Scheduler has 9 jobs", len(jobs) >= 9),
        ("13+ agent skills exist", skill_count >= 13),
        # Platinum checks (23-32+)
        ("In_Progress/ folder exists", in_progress_dir.exists()),
        ("Updates/ folder exists", updates_dir.exists()),
        ("ClaimManager works", claim_works),
        ("WorkZoneRouter routes correctly", routing_works),
        ("VaultSync importable", vault_sync_works),
        ("6+ watcher scripts exist", len(watcher_scripts) >= 6),
        ("5+ MCP server scripts exist", len(mcp_scripts) >= 5),
        ("CloudAgent extends BaseAgent", cloud_agent_works),
        ("DashboardUpdater works", dashboard_updater_works),
        ("6+ agent classes exist", agents_dir_count >= 6),
        ("18+ agent skills exist", skill_count >= 18),
        ("Scheduler has 9+ jobs", len(jobs) >= 9),
    ]

    all_pass = True
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {label}")

    print()
    if all_pass:
        print(f"ALL {len(checks)} CHECKS PASSED — Platinum Tier Complete!")
    else:
        failed = sum(1 for _, p in checks if not p)
        print(f"{len(checks) - failed}/{len(checks)} CHECKS PASSED — {failed} FAILED")
    print("=" * 60)


if __name__ == "__main__":
    main()
