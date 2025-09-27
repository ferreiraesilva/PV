# ADR-0005: Append-Only Audit Logging

- **Status**: Accepted
- **Date**: 2025-09-27

## Context
Regulatory and business constraints demand immutable tracking of every authenticated action, including diffs and metadata for forensic analysis.

## Decision
Implement an append-only `audit_logs` table in PostgreSQL. Write logs via middleware after each request, capturing masked payloads, diffs, and identity context. Expose only read-only APIs for querying with filters.

## Consequences
- **Positive**: Full traceability; supports investigations and compliance; simplifies audit trails.
- **Negative**: Storage growth over time; requires masking strategy to remove sensitive data; deletions only via archival or partition pruning.
