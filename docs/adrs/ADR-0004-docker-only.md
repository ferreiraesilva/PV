# ADR-0004: Docker-Only Deployment Strategy

- **Status**: Accepted
- **Date**: 2025-09-27

## Context
The client wants to operate entirely on local or self-managed infrastructure until product-market fit proves investment in cloud platforms worthwhile.

## Decision
Package the whole stack (app, PostgreSQL, observability tooling) using Docker and docker-compose. Avoid managed cloud services and keep artifacts portable.

## Consequences
- **Positive**: Easy local setup; deterministic environments; simple migration to on-premise servers.
- **Negative**: Manual scaling and failover; requires local resources for persistence and backups; extra care for security hardening.
