"""Print one deterministic example and an explicit correction."""
from dataclasses import asdict
from datetime import date
from decimal import Decimal
import json
from .domain import Agreement, Attendance, BillingPolicy, Occurrence, Outcome, Plan, calculate_charge


def main():
    agreement = Agreement('agr-101', 'demo-participant-7', Plan.PER_OCCURRENCE,
                          Decimal('35.00'), 'price-2026-Q4', date(2026, 10, 1))
    policy = BillingPolicy('billing-v1', charge_absences=False)
    occurrences = [
        Occurrence('slot-1', agreement.participant_id, date(2026, 10, 5), Outcome.HELD, Attendance.PRESENT),
        Occurrence('slot-2', agreement.participant_id, date(2026, 10, 12), Outcome.HELD, Attendance.ABSENT),
        Occurrence('slot-3', agreement.participant_id, date(2026, 10, 19), Outcome.PROVIDER_CANCELLED, Attendance.UNKNOWN),
    ]
    first = calculate_charge(agreement, policy, occurrences, '2026-10')
    corrected = calculate_charge(agreement, policy,
        [*occurrences[:1], Occurrence('slot-2', agreement.participant_id, date(2026, 10, 12), Outcome.HELD, Attendance.PRESENT), occurrences[2]],
        '2026-10', previous=first)
    def serialize(ch):
        r = asdict(ch)
        r['amount'] = str(ch.amount)
        for line in r['lines']:
            line['amount'] = str(line['amount'])
        return r
    print(json.dumps({'original': serialize(first), 'corrected': serialize(corrected)}, indent=2))

if __name__ == '__main__':
    main()
