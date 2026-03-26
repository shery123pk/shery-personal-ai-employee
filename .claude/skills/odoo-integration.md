---
name: odoo-integration
description: Odoo ERP integration via MCP server for invoicing and payments
priority: high
tier: platinum
---

# Skill: Odoo Integration

Interact with Odoo ERP for invoicing, payments, and accounting via MCP tools.

## Capabilities

### Invoice management
Create, list, and post invoices. Posting requires human approval.

### Payment processing
Register and confirm payments. Confirmation requires human approval.

### Account balance
Query account balances from Odoo's chart of accounts.

### DEV_MODE
Returns synthetic data when ODOO_DEV_MODE=true — no Odoo connection needed.

## MCP Tools

| Tool | Approval Required |
|------|-------------------|
| `create_invoice` | No |
| `list_invoices` | No |
| `post_invoice` | Yes |
| `create_payment` | No |
| `confirm_payment` | Yes |
| `get_account_balance` | No |

## Usage Examples

- "Create an invoice for Acme Corp for $5000"
- "List all draft invoices"
- "Post invoice #1001"
- "Check the bank account balance"

## Implementation

- MCP server: `scripts/mcp_odoo_server.py`
- Registration: `claude mcp add odoo-server -- python scripts/mcp_odoo_server.py`
- Docker: `deploy/docker-compose.odoo.yml` (Odoo 17 + PostgreSQL 15)

## Rules
- post_invoice and confirm_payment always require approval
- ODOO_DEV_MODE=true returns synthetic data
- Uses xmlrpc.client (stdlib — no external deps)
