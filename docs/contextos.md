# Domain Contexts

## Simulation Context
- Manages payment plan proposals, financial inputs, and calculation rules for PV, PMT, and FV.
- Provides ranking and comparative indicators for user decisions.
- Publishes summarized results for other contexts and audit logs.

## Receivables Portfolio Context
- Ingests historical contracts, payments, and risk signals.
- Calculates VPB, VPL, and pricing scenarios considering default and cancellation probabilities.
- Supplies normalized datasets for benchmarking and stores adjustments in audit trails.

## Benchmarking Context
- Aggregates anonymized metrics across tenants.
- Offers comparative KPIs (average PV, default rate, cancellations, pricing benchmarks) with filtering by segment and region.
- Enforces anonymization and data minimization policies.

## Recommendations Context
- Consumes outputs from simulation, portfolio, and benchmarking contexts.
- Holds rule-based placeholders for future ML-driven recommendations.
- Delivers insights and suggested actions back to the API with mandatory auditing.
