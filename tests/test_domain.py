import unittest
from datetime import date
from decimal import Decimal
from billability_lab.domain import Agreement, Attendance, BillingPolicy, Occurrence, Outcome, Plan, calculate_charge


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.agr = Agreement('a-1', 'u-1', Plan.PER_OCCURRENCE, Decimal('14.00'), 'price-v1', date(2026, 10, 1))
        self.policy = BillingPolicy('v1', False)

    def fact(self, ident, day, attendance=Attendance.PRESENT, outcome=Outcome.HELD):
        return Occurrence(ident, 'u-1', date(2026, 10, day), outcome, attendance)

    def charge(self, facts, policy=None, agreement=None, previous=None):
        return calculate_charge(agreement or self.agr, policy or self.policy, facts, '2026-10', previous)

    def test_billable_held_sessions(self):
        c = self.charge([self.fact('1', 3), self.fact('2', 4)])
        self.assertEqual(c.amount, Decimal('28.00'))
        self.assertEqual(len(c.lines), 2)

    def test_absence_is_not_billable_by_policy(self):
        c = self.charge([self.fact('1', 3, Attendance.ABSENT)])
        self.assertEqual(c.amount, Decimal('0.00'))

    def test_absence_can_be_billable_under_another_policy(self):
        c = self.charge([self.fact('1', 3, Attendance.ABSENT)], BillingPolicy('v2', True))
        self.assertEqual(c.amount, Decimal('14.00'))

    def test_provider_cancellation_not_billable_even_if_present(self):
        c = self.charge([self.fact('1', 3, Attendance.PRESENT, Outcome.PROVIDER_CANCELLED)])
        self.assertEqual(c.amount, Decimal('0.00'))

    def test_unknown_attendance_fails_closed_for_presence_policy(self):
        with self.assertRaisesRegex(ValueError, 'unknown'):
            self.charge([self.fact('1', 3, Attendance.UNKNOWN)])

    def test_order_independent_and_idempotent(self):
        a, b = self.fact('1', 3), self.fact('2', 5)
        first = self.charge([a, b])
        second = self.charge([b, a], previous=first)
        self.assertEqual(first, second)

    def test_correction_has_new_id_and_points_to_prior_charge(self):
        old = self.charge([self.fact('1', 3, Attendance.ABSENT)])
        new = self.charge([self.fact('1', 3, Attendance.PRESENT)], previous=old)
        self.assertNotEqual(old.id, new.id)
        self.assertEqual(new.supersedes, old.id)
        self.assertEqual(old.amount, Decimal('0.00'))
        self.assertEqual(new.amount, Decimal('14.00'))

    def test_duplicate_occurrence_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.charge([self.fact('1', 3), self.fact('1', 3)])

    def test_wrong_participant_rejected(self):
        with self.assertRaisesRegex(ValueError, 'participant'):
            self.charge([Occurrence('1', 'someone-else', date(2026, 10, 3), Outcome.HELD, Attendance.PRESENT)])

    def test_cross_cycle_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside cycle'):
            self.charge([Occurrence('1', 'u-1', date(2026, 9, 30), Outcome.HELD, Attendance.PRESENT)])

    def test_monthly_flat_independent_of_attendance(self):
        agr = Agreement('flat', 'u-1', Plan.MONTHLY_FLAT, Decimal('140.00'), 'p2', date(2026, 10, 1))
        c = self.charge([self.fact('1', 3, Attendance.ABSENT)], agreement=agr)
        self.assertEqual(c.amount, Decimal('140.00'))
        self.assertEqual(len(c.lines), 1)

    def test_price_version_is_part_of_snapshot_identity(self):
        changed = Agreement('a-1', 'u-1', Plan.PER_OCCURRENCE, Decimal('14.00'), 'price-v2', date(2026, 10, 1))
        self.assertNotEqual(self.charge([]).id, self.charge([], agreement=changed).id)

    def test_invalid_correction_scope_rejected(self):
        old = self.charge([])
        new_agr = Agreement('other', 'u-1', Plan.PER_OCCURRENCE, Decimal('14.00'), 'price-v1', date(2026, 10, 1))
        with self.assertRaisesRegex(ValueError, 'same agreement'):
            self.charge([], agreement=new_agr, previous=old)

    def test_invalid_money_precision_rejected(self):
        with self.assertRaises(ValueError):
            Agreement('x', 'u-1', Plan.MONTHLY_FLAT, Decimal('14.001'), 'v1', date(2026, 10, 1))

if __name__ == '__main__':
    unittest.main()
