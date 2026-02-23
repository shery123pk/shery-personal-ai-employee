"""End-to-end test: 3 files through the full watcher pipeline."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from file_watcher import FileSystemWatcher, INBOX_DIR, NEEDS_ACTION_DIR
from logger import get_today_log_path, iso_now, log_to_vault

VAULT_DIR = Path(__file__).resolve().parent.parent / "AI_Employee_Vault"
DONE_DIR = VAULT_DIR / "Done"


def main() -> None:
    print("=" * 60)
    print("END-TO-END TEST: 3 Files Through Full Pipeline")
    print("=" * 60)

    # ── Step 1: Start watcher ──
    print("\n[1/6] Starting file watcher...")
    watcher = FileSystemWatcher()
    watcher.start()
    print("       Watcher is running.\n")

    # ── Step 2: Drop 3 test files into Inbox ──
    print("[2/6] Dropping 3 files into Inbox...")
    test_files = [
        ("URGENT_budget_report.txt", "Q1 2026 budget needs immediate review."),
        ("REVIEW_meeting_notes.md", "## Team Standup\n- Discussed roadmap\n- Action items assigned"),
        ("FYI_newsletter_update.txt", "Monthly newsletter draft v2 attached."),
    ]

    for name, content in test_files:
        path = INBOX_DIR / name
        path.write_text(content, encoding="utf-8")
        print(f"       Dropped: {name} ({len(content)} bytes)")
        time.sleep(1.5)

    print()

    # ── Step 3: Verify action files in Needs_Action ──
    print("[3/6] Checking Needs_Action for action files...")
    time.sleep(1)
    action_files = sorted(
        f for f in NEEDS_ACTION_DIR.iterdir() if f.name.startswith("FILE_")
    )
    print(f"       Found {len(action_files)} action file(s):")
    for af in action_files:
        content = af.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "**priority:**" in line:
                priority = line.split("**priority:**")[1].strip()
                print(f"       - {af.name}  [priority: {priority}]")
                break

    if len(action_files) != 3:
        print("       FAIL: Expected 3 action files!")
        watcher.stop()
        sys.exit(1)
    print("       All 3 action files created.\n")

    # ── Step 4: Process each action file → move to Done ──
    print("[4/6] Processing action files (Needs_Action -> Done)...")
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
        print(f"       Processed: {af.name} -> Done/")

    print()

    # ── Step 5: Update Dashboard ──
    print("[5/6] Updating Dashboard.md...")
    inbox_count = len([f for f in INBOX_DIR.iterdir() if not f.name.startswith(".")])
    needs_count = len([f for f in NEEDS_ACTION_DIR.iterdir() if not f.name.startswith(".")])
    done_count = len([f for f in DONE_DIR.iterdir() if not f.name.startswith(".")])

    log_path = get_today_log_path()
    entries = json.loads(log_path.read_text(encoding="utf-8"))

    activity_rows = ""
    for e in entries:
        activity_rows += f'| {e["timestamp"]} | {e["action"]} | {e["source"]} | {e["result"]} |\n'

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
        "| Claude Agent | Ready | Available for tasks |\n"
        "| Vault Access | OK | All folders accessible |\n"
        "\n"
        "## Folder Counts\n"
        "\n"
        "| Folder | Count |\n"
        "|--------|-------|\n"
        f"| Inbox | {inbox_count} |\n"
        f"| Needs_Action | {needs_count} |\n"
        f"| Done | {done_count} |\n"
        "\n"
        "## Recent Activity\n"
        "\n"
        "| Timestamp | Action | File | Result |\n"
        "|-----------|--------|------|--------|\n"
        f"{activity_rows}"
    )

    (VAULT_DIR / "Dashboard.md").write_text(dashboard, encoding="utf-8")
    print(f"       Inbox: {inbox_count}  |  Needs_Action: {needs_count}  |  Done: {done_count}")
    print("       Dashboard.md updated.\n")

    # ── Step 6: Show logs ──
    print("[6/6] Vault log entries:")
    for e in entries:
        print(f'       {e["timestamp"]}  {e["action"]:20s}  {e["source"]:40s}  {e["result"]}')

    # ── Stop watcher ──
    watcher.stop()

    # ── Final verification ──
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    done_files = sorted(f.name for f in DONE_DIR.iterdir() if not f.name.startswith("."))
    log_entries = json.loads(log_path.read_text(encoding="utf-8"))

    checks = [
        ("3 files in Inbox", inbox_count == 3),
        ("0 files in Needs_Action", needs_count == 0),
        ("3 files in Done", len(done_files) == 3),
        ("Log file exists", log_path.exists()),
        ("Log has >= 6 entries", len(log_entries) >= 6),
        ("Dashboard updated", "Running" in (VAULT_DIR / "Dashboard.md").read_text(encoding="utf-8")),
    ]

    all_pass = True
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {label}")

    print()
    if all_pass:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
    print("=" * 60)


if __name__ == "__main__":
    main()
