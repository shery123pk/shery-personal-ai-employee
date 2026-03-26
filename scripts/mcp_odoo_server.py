"""MCP Odoo Server — FastMCP stdio server with Odoo ERP tools.

Provides 6 tools for Claude Code to interact with Odoo:
- create_invoice: Create a new customer invoice
- list_invoices: List invoices with optional filtering
- post_invoice: Post/confirm an invoice (requires approval)
- create_payment: Register a payment
- confirm_payment: Confirm a payment (requires approval)
- get_account_balance: Get account balance summary

Registration:
    claude mcp add odoo-server -- python scripts/mcp_odoo_server.py

In DEV_MODE: returns synthetic data, no Odoo connection.
"""

import json
import sys
import xmlrpc.client
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import ODOO_DB, ODOO_DEV_MODE, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME

mcp = FastMCP("odoo-server")


# ---------------------------------------------------------------------------
# Odoo client
# ---------------------------------------------------------------------------

class OdooClient:
    """XML-RPC client for Odoo ERP."""

    def __init__(self) -> None:
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        self._uid: int | None = None

    def authenticate(self) -> int:
        """Authenticate and return user ID."""
        if self._uid is not None:
            return self._uid
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self._uid = common.authenticate(self.db, self.username, self.password, {})
        return self._uid

    def execute(self, model: str, method: str, *args, **kwargs) -> object:
        """Execute an Odoo model method via XML-RPC."""
        uid = self.authenticate()
        models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return models.execute_kw(
            self.db, uid, self.password,
            model, method, list(args), kwargs,
        )


_client = OdooClient()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def create_invoice(partner_name: str, amount: float, description: str = "") -> str:
    """Create a new customer invoice in Odoo.

    Args:
        partner_name: Customer/partner name.
        amount: Invoice total amount.
        description: Optional invoice description.

    Returns:
        JSON with invoice ID or synthetic result in DEV_MODE.
    """
    if ODOO_DEV_MODE:
        return json.dumps({
            "status": "created",
            "invoice_id": 1001,
            "partner": partner_name,
            "amount": amount,
            "description": description,
            "mode": "dev",
        })

    try:
        invoice_id = _client.execute(
            "account.move", "create",
            [{
                "move_type": "out_invoice",
                "partner_id": partner_name,
                "invoice_line_ids": [(0, 0, {
                    "name": description or "Service",
                    "quantity": 1,
                    "price_unit": amount,
                })],
            }],
        )
        return json.dumps({"status": "created", "invoice_id": invoice_id})
    except Exception as exc:
        return json.dumps({"status": "error", "detail": str(exc)})


@mcp.tool()
def list_invoices(state: str = "draft", limit: int = 20) -> str:
    """List invoices from Odoo with optional state filter.

    Args:
        state: Invoice state filter (draft, posted, cancel). Default: draft.
        limit: Max results. Default: 20.

    Returns:
        JSON list of invoices.
    """
    if ODOO_DEV_MODE:
        return json.dumps({
            "invoices": [
                {"id": 1001, "name": "INV/2026/0001", "state": state, "amount": 1500.00, "partner": "Acme Corp"},
                {"id": 1002, "name": "INV/2026/0002", "state": state, "amount": 750.00, "partner": "Beta LLC"},
            ],
            "total": 2,
            "mode": "dev",
        })

    try:
        invoices = _client.execute(
            "account.move", "search_read",
            [[("move_type", "=", "out_invoice"), ("state", "=", state)]],
            fields=["name", "state", "amount_total", "partner_id"],
            limit=limit,
        )
        return json.dumps({"invoices": invoices, "total": len(invoices)})
    except Exception as exc:
        return json.dumps({"status": "error", "detail": str(exc)})


@mcp.tool()
def post_invoice(invoice_id: int) -> str:
    """Post/confirm an invoice (requires approval).

    This creates an approval request — the invoice is NOT posted directly.

    Args:
        invoice_id: Odoo invoice ID to post.

    Returns:
        JSON with approval request status.
    """
    if ODOO_DEV_MODE:
        return json.dumps({
            "status": "approval_requested",
            "invoice_id": invoice_id,
            "message": "Invoice posting requires human approval",
            "mode": "dev",
        })

    from approval_utils import create_approval_request
    path = create_approval_request(
        action_type="post_invoice",
        summary=f"Post invoice #{invoice_id}",
        details={"invoice_id": invoice_id},
        domain="finance",
    )
    return json.dumps({"status": "approval_requested", "file": path.name})


@mcp.tool()
def create_payment(partner_name: str, amount: float, journal: str = "Bank") -> str:
    """Register a payment in Odoo.

    Args:
        partner_name: Customer/partner name.
        amount: Payment amount.
        journal: Payment journal (Bank, Cash). Default: Bank.

    Returns:
        JSON with payment ID or synthetic result.
    """
    if ODOO_DEV_MODE:
        return json.dumps({
            "status": "created",
            "payment_id": 2001,
            "partner": partner_name,
            "amount": amount,
            "journal": journal,
            "mode": "dev",
        })

    try:
        payment_id = _client.execute(
            "account.payment", "create",
            [{
                "partner_id": partner_name,
                "amount": amount,
                "journal_id": journal,
                "payment_type": "inbound",
            }],
        )
        return json.dumps({"status": "created", "payment_id": payment_id})
    except Exception as exc:
        return json.dumps({"status": "error", "detail": str(exc)})


@mcp.tool()
def confirm_payment(payment_id: int) -> str:
    """Confirm a payment (requires approval).

    Args:
        payment_id: Odoo payment ID to confirm.

    Returns:
        JSON with approval request status.
    """
    if ODOO_DEV_MODE:
        return json.dumps({
            "status": "approval_requested",
            "payment_id": payment_id,
            "message": "Payment confirmation requires human approval",
            "mode": "dev",
        })

    from approval_utils import create_approval_request
    path = create_approval_request(
        action_type="confirm_payment",
        summary=f"Confirm payment #{payment_id}",
        details={"payment_id": payment_id},
        domain="finance",
    )
    return json.dumps({"status": "approval_requested", "file": path.name})


@mcp.tool()
def get_account_balance(account_code: str = "1000") -> str:
    """Get account balance summary from Odoo.

    Args:
        account_code: Account code to query. Default: 1000 (bank).

    Returns:
        JSON with balance information.
    """
    if ODOO_DEV_MODE:
        return json.dumps({
            "account_code": account_code,
            "balance": 25000.00,
            "debit": 50000.00,
            "credit": 25000.00,
            "currency": "USD",
            "mode": "dev",
        })

    try:
        accounts = _client.execute(
            "account.account", "search_read",
            [[("code", "=", account_code)]],
            fields=["name", "code", "current_balance"],
            limit=1,
        )
        if accounts:
            return json.dumps({"account": accounts[0]})
        return json.dumps({"status": "not_found", "account_code": account_code})
    except Exception as exc:
        return json.dumps({"status": "error", "detail": str(exc)})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
