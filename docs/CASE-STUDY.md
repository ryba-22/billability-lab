# Case study: attendance is not a financial decision

**Scope:** small standalone, original simulation with fictional facts. **Status:** local demonstration; no customer deployment or accounting integration.

## Problem

A calendar may say an event was held, cancelled or attended. Those are operational facts, not a complete answer to whether money is owed. Basing charges directly on an attendance column makes missing records and policy changes financially consequential without an explicit decision.

## Competing models

- **Direct calculation**: `charge = count(present events) × unit price`. Short, but it silently assumes `present == billable` and makes policy changes hard to reconstruct.
- **Fact → policy → charge**: occurrences describe what happened, an effective agreement establishes the financial terms, and a versioned policy decides billability. Selected for this deliberately small lab.

## Reproducible experiment

From the repository root:

```bash
python -m billability_lab.demo
python -m unittest discover -s tests -v
```

The sample computes an original **35.00** amount and then a corrected **70.00** amount after a changed occurrence fact. The correction references the earlier charge ID, and the earlier value is not mutated. The same inputs create the same digest/identity; reordered source events produce the same result.

The tests cover unknown attendance (fail closed under an attendance-dependent policy), duplicated source facts, policy differences, cancellations, corrections, and the invariant `SUM(lines) = charge.amount`.

## Decision and trade-off

Keep calculation pure and snapshots immutable. This improves inspectability while intentionally deferring storage, transactional boundaries, race conditions, payment allocation and operator approval to a hypothetical host system. The demonstration does not establish financial compliance or production safety.

## What could falsify the model?

A subscription that starts mid-month, retroactive pricing changes, multiple legal settlement entities or a cancellation that remains billable would require new domain policies or an expanded agreement lifecycle. This tiny lab makes such unknowns visible rather than hiding them in a conditional.

## What this evidence establishes

Executable handling of one narrow type of financial rule with concrete test cases. It **does not** establish correctness of any private billing system, operational adoption, or production outcomes. Authorship and suitability for public portfolio use must be reviewed by the owner.
