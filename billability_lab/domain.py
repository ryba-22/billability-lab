"""Synthetic billing domain. No database, external services, or customer data."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json

MONEY = Decimal('0.01')


class Plan(str, Enum):
    PER_OCCURRENCE = 'per_occurrence'
    MONTHLY_FLAT = 'monthly_flat'


class Outcome(str, Enum):
    HELD = 'held'
    PROVIDER_CANCELLED = 'provider_cancelled'


class Attendance(str, Enum):
    PRESENT = 'present'
    ABSENT = 'absent'
    UNKNOWN = 'unknown'


@dataclass(frozen=True)
class Agreement:
    id: str
    participant_id: str
    plan: Plan
    amount: Decimal
    price_version: str
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self):
        if self.amount < 0 or self.amount != self.amount.quantize(MONEY):
            raise ValueError('amount must be non-negative, with two decimals')
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError('invalid effective dates')
        if not self.id or not self.price_version:
            raise ValueError('agreement and price version must be explicit')


@dataclass(frozen=True)
class Occurrence:
    id: str
    participant_id: str
    on: date
    outcome: Outcome
    attendance: Attendance


@dataclass(frozen=True)
class BillingPolicy:
    version: str
    # Only affects per-occurrence billing. Unknown attendance fails closed when false.
    charge_absences: bool
    # Provider cancellation is always non-billable in this sample policy.


@dataclass(frozen=True)
class ChargeLine:
    source_id: str
    reason: str
    amount: Decimal


@dataclass(frozen=True)
class Charge:
    id: str
    agreement_id: str
    cycle: str
    policy_version: str
    price_version: str
    amount: Decimal
    lines: tuple[ChargeLine, ...]
    facts_digest: str
    supersedes: str | None = None

    def __post_init__(self):
        if sum((line.amount for line in self.lines), Decimal('0.00')) != self.amount:
            raise ValueError('lines do not sum to charge amount')


def _period(cycle: str) -> tuple[date, date]:
    try:
        if len(cycle) != 7 or cycle[4] != '-':
            raise ValueError()
        y, m = int(cycle[:4]), int(cycle[5:])
        start = date(y, m, 1)
        end = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
        return start, end
    except (ValueError, TypeError) as exc:
        raise ValueError('cycle must be YYYY-MM') from exc


def calculate_charge(agreement: Agreement, policy: BillingPolicy,
                     occurrences: list[Occurrence], cycle: str,
                     previous: Charge | None = None) -> Charge:
    """Pure calculation: same agreement, facts, policy and cycle => same charge ID.

    A changed snapshot generates a new identity. A correction is explicit via `previous`;
    this does not mutate the prior Charge or allocate payments.
    """
    start, end = _period(cycle)
    if not policy.version:
        raise ValueError('policy version must be explicit')
    if agreement.effective_from >= end or (agreement.effective_to and agreement.effective_to < start):
        raise ValueError('agreement not active in requested month')
    if len({o.id for o in occurrences}) != len(occurrences):
        raise ValueError('duplicate occurrence id')
    for occ in occurrences:
        if occ.participant_id != agreement.participant_id:
            raise ValueError(f'wrong participant in {occ.id}')
        if not (start <= occ.on < end):
            raise ValueError(f'occurrence outside cycle: {occ.id}')
        if occ.on < agreement.effective_from or (agreement.effective_to and occ.on > agreement.effective_to):
            raise ValueError(f'occurrence outside agreement period: {occ.id}')

    sorted_facts = sorted(occurrences, key=lambda o: (o.on.isoformat(), o.id))
    lines: list[ChargeLine] = []
    if agreement.plan == Plan.MONTHLY_FLAT:
        # No proration: explicit product decision, not a default hidden in a formula.
        lines.append(ChargeLine(f'cycle:{cycle}', 'contracted monthly amount', agreement.amount))
    elif agreement.plan == Plan.PER_OCCURRENCE:
        for occ in sorted_facts:
            if occ.outcome == Outcome.PROVIDER_CANCELLED:
                continue
            if occ.attendance == Attendance.UNKNOWN and not policy.charge_absences:
                raise ValueError(f'attendance unknown: {occ.id}; cannot infer billability')
            billable = policy.charge_absences or occ.attendance == Attendance.PRESENT
            if billable:
                lines.append(ChargeLine(occ.id, 'held, billable under policy', agreement.amount))
    else:
        raise ValueError('unsupported plan')

    payload = {
        'agreement': {'id': agreement.id, 'participant': agreement.participant_id,
                      'plan': agreement.plan.value, 'amount': str(agreement.amount),
                      'price_version': agreement.price_version,
                      'from': agreement.effective_from.isoformat(),
                      'to': agreement.effective_to.isoformat() if agreement.effective_to else None},
        'policy': {'version': policy.version, 'charge_absences': policy.charge_absences},
        'cycle': cycle,
        'facts': [{'id': o.id, 'on': o.on.isoformat(), 'participant': o.participant_id,
                   'outcome': o.outcome.value, 'attendance': o.attendance.value}
                  for o in sorted_facts],
    }
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    charge_id = f'ch_{digest[:20]}'
    if previous is not None:
        if previous.agreement_id != agreement.id or previous.cycle != cycle:
            raise ValueError('correction must apply to the same agreement and cycle')
        if previous.id == charge_id:
            return previous  # repeated calculation is idempotent
    return Charge(charge_id, agreement.id, cycle, policy.version, agreement.price_version,
                  sum((line.amount for line in lines), Decimal('0.00')),
                  tuple(lines), digest, previous.id if previous else None)
