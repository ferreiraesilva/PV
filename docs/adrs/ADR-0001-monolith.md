# ADR-0001: Monolith Architecture

- **Status**: Accepted
- **Date**: 2025-09-27

## Context
safv requires cohesive coordination between financial simulations, receivables valuation, benchmarking, auditing, and user management. The team wants fast iteration without the operational overhead of deploying and maintaining multiple services.

## Decision
Adopt a single FastAPI monolith that encapsulates API, domain logic, and persistence layers. Modules remain logically separated inside the monolith to allow future extraction if needed.

## Consequences
- **Positive**: Simplifies deployment with a single Docker image; enables straightforward transactions across features; reduces infrastructure cost.
- **Negative**: Codebase can become large; requires discipline to maintain modular boundaries; scaling is limited to vertical or replica-based approaches.
