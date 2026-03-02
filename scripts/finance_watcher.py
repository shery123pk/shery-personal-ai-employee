"""Finance Watcher — monitors CSV files for financial transactions.

Extends BaseWatcher. Watches the Finance/ folder for new CSV files,
parses transactions, detects anomalies (high amounts, duplicates),
and creates action items in Needs_Action/.

Usage:
    python scripts/finance_watcher.py
"""

import csv
import io
import signal
import sys
import time
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import FINANCE_CSV_DIR, NEEDS_ACTION_DIR
from file_watcher import BaseWatcher
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("finance_watcher")

# Anomaly thresholds
HIGH_AMOUNT_THRESHOLD = 5000.0
DUPLICATE_WINDOW_DAYS = 7


class FinanceHandler(FileSystemEventHandler):
    """Watchdog handler that delegates CSV files to FinanceWatcher."""

    def __init__(self, watcher: "FinanceWatcher") -> None:
        super().__init__()
        self.watcher = watcher

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == ".csv" and not file_path.name.startswith("."):
            self.watcher.on_new_file(file_path)


class FinanceWatcher(BaseWatcher):
    """Monitors Finance/ folder for new CSV transaction files."""

    def __init__(self) -> None:
        self._observer = Observer()
        self._running = False

    def start(self) -> None:
        """Start monitoring Finance/ folder for new CSV files."""
        FINANCE_CSV_DIR.mkdir(parents=True, exist_ok=True)
        NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)

        # Scan existing CSVs
        self._scan_existing()

        handler = FinanceHandler(self)
        self._observer.schedule(handler, str(FINANCE_CSV_DIR), recursive=False)
        self._observer.start()
        self._running = True

        log_to_vault("finance_watcher_started", "finance_watcher", "success")
        logger.info("Finance watcher started — monitoring %s", FINANCE_CSV_DIR)

    def stop(self) -> None:
        """Stop the finance watcher."""
        if self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            log_to_vault("finance_watcher_stopped", "finance_watcher", "success")
            logger.info("Finance watcher stopped.")

    def on_new_file(self, file_path: Path) -> None:
        """Parse CSV transaction file and create action items for anomalies."""
        try:
            transactions = self._parse_transactions(file_path)
            anomalies = self._detect_anomalies(transactions)

            logger.info(
                "Parsed %d transactions from %s, found %d anomalies",
                len(transactions), file_path.name, len(anomalies),
            )

            # Create action items for anomalies
            for anomaly in anomalies:
                self._create_anomaly_action(file_path.name, anomaly)

            # Log summary
            total_amount = sum(t.get("amount", 0) for t in transactions)
            log_to_vault(
                "finance_csv_processed",
                file_path.name,
                "success",
                transactions=str(len(transactions)),
                anomalies=str(len(anomalies)),
                total_amount=f"{total_amount:.2f}",
            )

        except Exception as exc:
            logger.error("Error processing %s: %s", file_path.name, exc)
            log_to_vault("finance_csv_error", file_path.name, "error", detail=str(exc))

    def _parse_transactions(self, csv_path: Path) -> list[dict]:
        """Parse CSV into transaction records."""
        transactions = []
        content = csv_path.read_text(encoding="utf-8")
        reader = csv.DictReader(io.StringIO(content))

        for row in reader:
            try:
                amount = float(row.get("amount", "0"))
            except (ValueError, TypeError):
                amount = 0.0

            transactions.append({
                "date": row.get("date", ""),
                "description": row.get("description", ""),
                "amount": amount,
                "category": row.get("category", "Unknown"),
                "type": row.get("type", "expense"),
            })

        return transactions

    def _detect_anomalies(self, transactions: list[dict]) -> list[dict]:
        """Flag unusual transactions (high amounts, subscriptions, unknown categories)."""
        anomalies = []

        for txn in transactions:
            reasons = []

            # High amount
            if txn["amount"] >= HIGH_AMOUNT_THRESHOLD:
                reasons.append(f"High amount: ${txn['amount']:.2f}")

            # Unknown category
            if txn["category"].lower() in ("unknown", "uncategorised", "uncategorized", "other"):
                reasons.append(f"Unknown category: {txn['category']}")

            # Suspicious keywords
            suspicious = ("suspicious", "fraud", "unauthorized", "unusual")
            if any(kw in txn["description"].lower() for kw in suspicious):
                reasons.append(f"Suspicious description: {txn['description']}")

            if reasons:
                anomalies.append({**txn, "anomaly_reasons": reasons})

        return anomalies

    def _create_anomaly_action(self, source_file: str, anomaly: dict) -> None:
        """Create a Needs_Action item for a financial anomaly."""
        desc = anomaly.get("description", "unknown")
        slug = desc.lower().replace(" ", "_")[:30]
        filename = f"FINANCE_{slug}.md"
        path = NEEDS_ACTION_DIR / filename

        reasons = "\n".join(f"  - {r}" for r in anomaly.get("anomaly_reasons", []))

        content = (
            f"# Financial Anomaly: {desc}\n\n"
            f"- **source_file:** {source_file}\n"
            f"- **date:** {anomaly.get('date', 'unknown')}\n"
            f"- **amount:** ${anomaly.get('amount', 0):.2f}\n"
            f"- **category:** {anomaly.get('category', 'unknown')}\n"
            f"- **type:** {anomaly.get('type', 'unknown')}\n"
            f"- **priority:** URGENT\n"
            f"- **status:** pending\n\n"
            f"## Anomaly Reasons\n\n"
            f"{reasons}\n\n"
            f"---\n\n"
            f"Detected at: {iso_now()}\n"
        )

        path.write_text(content, encoding="utf-8")
        logger.info("Created anomaly action: %s", filename)

    def _scan_existing(self) -> None:
        """Process CSV files already in Finance/ at startup."""
        for item in FINANCE_CSV_DIR.iterdir():
            if item.is_file() and item.suffix.lower() == ".csv" and not item.name.startswith("."):
                action_exists = any(
                    f.name.startswith("FINANCE_") for f in NEEDS_ACTION_DIR.iterdir()
                    if f.is_file()
                ) if NEEDS_ACTION_DIR.exists() else False
                if not action_exists:
                    self.on_new_file(item)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    watcher = FinanceWatcher()

    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Shutdown signal received.")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    watcher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    main()
