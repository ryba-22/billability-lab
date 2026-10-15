# Billability Lab

**A small executable example of why attendance, billability and charges are different concepts.**

This is an original **synthetic** case study, not an extraction of a commercial system. It intentionally models *one monthly charge per participant and agreement*, under one of two plans:

- `per_occurrence`: held sessions are billed based on an explicitly versioned attendance policy; provider cancellations are not billed.
- `monthly_flat`: a contracted monthly amount is billed independently of individual attendance.

## Try it

Python 3.11+; no dependencies or accounts.

```sh
python -m billability_lab.demo
python -m unittest discover -s tests -v
```

The demo computes an original October charge and a separate, explicit correction. Each result has deterministic identity derived from its source facts, agreement, price version and policy version.

## Domain boundaries and guarantees

`Occurrence` is an observed fact. `BillingPolicy` decides billability. `Agreement` binds terms to a participant. `Charge` is the immutable calculated outcome. **Presence is not a Charge. A price version is not a payment.**

- Source IDs cannot be duplicated within a calculation.
- Unknown attendance causes a failure when presence affects billability; it is never silently treated as absent.
- Correcting a fact produces a new Charge that references the old Charge without mutating history.
- Identical inputs (including reordered facts) produce identical identities.
- Sum of ChargeLines equals Charge.amount.
- Price/policy versions belong to the Charge snapshot.

## What this deliberately does **not** claim

No persistence, allocation of payments, legal-entity handling, proration, concurrency, timezone resolution, refund logic or production readiness. A financial system would need these properties and tests before handling real money. The agreement has only a simplified activation window; backdated enrollment changes need a real policy.

## Evidence-backed case study

[Problem, alternatives, experiments and limits](docs/CASE-STUDY.md).

## Structure

- `billability_lab/domain.py` — pure domain calculation and invariants
- `billability_lab/demo.py` — executable correction scenario
- `tests/` — counterexamples, ordering, invalid inputs and correction tests
- `docs/DECISIONS.md` — choices and alternatives

**Portfolio claim:** I can separate facts from policies and outcomes, make assumptions explicit, and encode invariants in tests. It is not a claim that a billing product has been deployed.
