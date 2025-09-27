# ADR-0003: PostgreSQL as Primary Database

- **Status**: Accepted
- **Date**: 2025-09-27

## Context
Financial workloads demand strong transactional guarantees, advanced data types (JSONB), and robust indexing. Audit requirements need append-only storage with retention policies.

## Decision
Adopt PostgreSQL as the main relational database. Use SQLAlchemy for ORM mapping and leverage PostgreSQL features like JSONB, window functions, and partitioning.

## Consequences
- **Positive**: Mature ecosystem, reliable transactions, strong tooling, native JSONB for diffs.
- **Negative**: Requires tuning for large datasets; operational management handled via Docker instead of managed services.
