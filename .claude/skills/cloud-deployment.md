---
name: cloud-deployment
description: Deploy and manage the Cloud VM AI Employee instance
priority: high
tier: platinum
---

# Skill: Cloud Deployment

Deploy and manage the AI Employee Cloud VM for 24/7 autonomous operation.

## Capabilities

### Docker deployment
Build and run the full Cloud stack (AI Employee + Odoo + PostgreSQL) via `deploy/docker-compose.yml`.

### Systemd deployment
Deploy directly on an Oracle/AWS VM using `deploy/ai-employee.service`.

### Health monitoring
HTTP `/health` endpoint on port 8080 returns JSON status of all components.

### Cloud entrypoint
Single process `scripts/cloud_entrypoint.py` starts GmailWatcher, SyncWatcher, scheduler, health monitor, and autonomous loop.

## Usage Examples

- "Deploy the AI Employee to the cloud VM"
- "Check the cloud health endpoint"
- "Start the Docker stack with Odoo"
- "View cloud deployment logs"

## Implementation

- Dockerfile: `deploy/Dockerfile`
- Docker Compose: `deploy/docker-compose.yml`
- Systemd: `deploy/ai-employee.service`
- Entrypoint: `scripts/cloud_entrypoint.py`
- Health: `scripts/health_monitor.py`

## Rules
- Always set WORK_ZONE=cloud for Cloud deployments
- Health endpoint must be accessible on CLOUD_HEALTH_PORT
- Graceful shutdown via SIGINT/SIGTERM
