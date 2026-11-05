import dataclasses
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from payment_processor import PaymentProcessor, Receipt, CurrencyRegion  # noqa: E402


class TestFees(unittest.TestCase):
    def test_first_tier(self):
        self.assertEqual(PaymentProcessor.calculate_fee(Decimal("100")), Decimal("1.50"))

    def test_fee_is_marginal_across_tiers(self):
        # 1000 at 1.5% + 1000 at 1.2% = 15 + 12
        self.assertEqual(PaymentProcessor.calculate_fee(Decimal("2000")), Decimal("27.00"))

    def test_top_tier(self):
        # 15 (first 1000) + 48 (next 4000 at 1.2%) + 25 (2500 at 1%)
        self.assertEqual(PaymentProcessor.calculate_fee(Decimal("7500")), Decimal("88.00"))

    def test_larger_payment_never_has_smaller_fee(self):
        just_below = PaymentProcessor.calculate_fee(Decimal("1000.00"))
        just_above = PaymentProcessor.calculate_fee(Decimal("1000.01"))
        self.assertGreaterEqual(just_above, just_below)


class TestPayments(unittest.TestCase):
    def setUp(self):
        self.p = PaymentProcessor()

    def test_receipt_contents(self):
        r = self.p.process_payment("100.00", "GBP")
        self.assertIsInstance(r, Receipt)
        self.assertEqual(r.amount, Decimal("100.00"))
        self.assertEqual(r.region, CurrencyRegion.UK)
        self.assertEqual(r.total, Decimal("101.50"))
        self.assertTrue(r.transaction_id)

    def test_eu_tax_applied(self):
        r = self.p.process_payment("200.00", "EUR")
        self.assertEqual(r.tax, Decimal("30.00"))

    def test_no_float_errors(self):
        r = self.p.process_payment("0.10", "USD")
        self.assertEqual(r.amount + r.amount + r.amount, Decimal("0.30"))

    def test_invalid_amounts_rejected(self):
        for amount in ("0", "-5"):
            with self.assertRaises(ValueError):
                self.p.process_payment(amount, "GBP")

    def test_unknown_currency_rejected(self):
        with self.assertRaises(ValueError):
            self.p.process_payment("10", "XYZ")
        self.assertEqual(len(self.p.get_transaction_history()), 0)

    def test_discount(self):
        self.assertEqual(self.p.apply_discount("SAVE10", "100"), Decimal("90.00"))
        self.assertEqual(self.p.apply_discount("UNKNOWN", "100"), Decimal("100.00"))


class TestImmutability(unittest.TestCase):
    def setUp(self):
        self.p = PaymentProcessor()
        self.p.process_payment("100", "GBP")

    def test_history_cannot_be_cleared(self):
        history = self.p.get_transaction_history()
        with self.assertRaises(AttributeError):
            history.clear()  # tuples have no clear()
        self.assertEqual(len(self.p.get_transaction_history()), 1)

    def test_receipts_cannot_be_changed(self):
        receipt = self.p.get_transaction_history()[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            receipt.amount = Decimal("1")

    def test_audit_trail_records_each_payment(self):
        self.p.process_payment("50", "USD")
        trail = self.p.audit_trail()
        self.assertEqual([e.action for e in trail], ["payment_processed"] * 2)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            trail[0].details = "tampered"


if __name__ == "__main__":
    unittest.main()
