# ADR-0002: FastAPI for the Web Layer

- **Status**: Accepted
- **Date**: 2025-09-27

## Context
We need an async-friendly Python framework with first-class OpenAPI support, dependency injection for security policies, and good ecosystem adoption.

## Decision
Use FastAPI as the primary HTTP framework. Combine it with Pydantic for validation, dependency injection for RBAC, and Starlette middleware for auditing and observability.

## Consequences
- **Positive**: Automatic OpenAPI generation; high performance with uvicorn; straightforward integration with Pydantic and async SQLAlchemy.
- **Negative**: Framework evolution is rapid; requires careful testing when upgrading; some advanced features (e.g., background jobs) need extra libraries.
