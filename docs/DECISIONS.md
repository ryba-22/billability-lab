# Decisions and trade-offs

## Why one calculated Charge per cycle?

A monthly aggregation makes cross-session billability visible. It also requires explicit source-line traceability. A per-session Charge model could be valid under a different collection/settlement workflow.

## Why immutable corrections?

An updated attendance fact must not erase the basis for a previously communicated amount. Recalculation can produce a different candidate; in a real system, publishing it would require a separate approval/adjustment process.

## Why fail on unknown attendance?

For attendance-dependent billing, no attendance record is **not** proof of absence. Silent defaults would turn missing data into monetary decisions.

## Why no persistence?

The portfolio goal is to demonstrate domain boundaries and behavior without pretending to solve transactional concurrency, accounting or funds allocation.

## Alternatives deliberately not selected

- Mutable totals: simpler implementation, weaker auditability.
- Recompute prior Charge using today's policy: easier, but loses reproducibility.
- Treat attendance as intrinsically billable: confuses facts and financial decisions.
