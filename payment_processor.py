import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class CurrencyRegion(Enum):
    UK = "UK"
    US = "US"
    EU = "EU"
    CRYPTO = "CRYPTO"

@dataclass
class AuditEvent:
    action: str
    timestamp: datetime
    details: str

@dataclass
class Receipt:
    transaction_id: str
    amount: float
    currency: str
    timestamp: datetime
    fee: float = 0.0
    tax: float = 0.0

# Tiered fee structure: (max_amount, fee_percentage)
FEE_TIERS = [
    (1000, 0.015),  # 0-1000: 1.5%
    (5000, 0.012),  # 1000-5000: 1.2%
    (float("inf"), 0.01),  # 5000+: 1.0%
]

# Regional tax rates by currency origin
REGIONAL_TAX_RATES = {
    "GBP": 0.0,  # UK: no tax
    "USD": 0.0,  # US: no tax
    "EUR": 0.15,  # EU: 15% tax
    "BTC": 0.0,  # Crypto: no tax (regulatory uncertainty)
    "ETH": 0.0,  # Crypto: no tax
}

# Supported cryptocurrencies
CRYPTO_CURRENCIES = {"BTC", "ETH"}

class PaymentProcessor:
    def __init__(self):
        # We use a private attribute to store the history
        self._history = []
        self._audit_trail: list[AuditEvent] = []

    def _get_region(self, currency: str) -> CurrencyRegion:
        """Determine the region based on currency origin."""
        if currency in CRYPTO_CURRENCIES:
            return CurrencyRegion.CRYPTO
        if currency == "GBP":
            return CurrencyRegion.UK
        if currency == "USD":
            return CurrencyRegion.US
        if currency == "EUR":
            return CurrencyRegion.EU
        return CurrencyRegion.US  # default

    def _calculate_tiered_fee(self, amount: float) -> float:
        """Calculate fee using tiered percentage structure."""
        for max_amount, fee_percentage in FEE_TIERS:
            if amount <= max_amount:
                return amount * fee_percentage
        return amount * FEE_TIERS[-1][1]  # fallback to lowest tier

    def _calculate_tax(self, amount: float, currency: str) -> float:
        """Calculate regional tax based on currency origin."""
        tax_rate = REGIONAL_TAX_RATES.get(currency, 0.0)
        return amount * tax_rate

    def process_payment(self, amount: float, currency: str) -> Receipt:
        # 1. Generate a unique ID (using uuid4 for professional standards)
        txn_id = str(uuid.uuid4())

        # 2. Calculate fee using tiered structure
        fee = self._calculate_tiered_fee(amount)

        # 3. Calculate regional tax
        tax = self._calculate_tax(amount, currency)

        # 4. Create the receipt object
        receipt = Receipt(
            transaction_id=txn_id,
            amount=amount,
            currency=currency,
            timestamp=datetime.now(),
            fee=fee,
            tax=tax,
        )

        # 5. Save it to our internal records
        self._history.append(receipt)

        # 6. Add audit event
        self._audit_trail.append(
            AuditEvent(
                action="payment_processed",
                timestamp=datetime.now(),
                details=f"Transaction {txn_id}: {amount} {currency}, fee={fee:.2f}, tax={tax:.2f}",
            )
        )

        return receipt

    def apply_discount(self, code: str, amount: float) -> float:
        # Check for the specific 'SAVE10' business rule
        if code == "SAVE10":
            return amount * 0.9
        return amount

    def calculate_fee(self, amount: float) -> float:
        # Tiered percentage fee structure
        return self._calculate_tiered_fee(amount)

    def get_transaction_history(self) -> list[Receipt]:
        # CRITICAL: Return a COPY of the list.
        # If we just 'return self._history', the user can clear() our data.
        return list(self._history)

    def audit_trail(self) -> list[AuditEvent]:
        """Return the audit trail of all operations."""
        return list(self._audit_trail)


# ============================================
# Acceptance Tests
# ============================================

def test_process_payment_returns_receipt():
    p = PaymentProcessor()
    receipt = p.process_payment(100.0, "GBP")
    assert isinstance(receipt, Receipt)
    assert receipt.amount == 100.0
    assert receipt.currency == "GBP"
    assert receipt.transaction_id != ""

def test_transaction_history_grows():
    p = PaymentProcessor()
    p.process_payment(50.0, "GBP")
    p.process_payment(75.0, "USD")
    assert len(p.get_transaction_history()) == 2

def test_discount_reduces_amount():
    p = PaymentProcessor()
    result = p.apply_discount("SAVE10", 100.0)
    assert result == 90.0

def test_fee_calculation():
    p = PaymentProcessor()
    fee = p.calculate_fee(100.0)
    assert abs(fee - 1.5) < 0.01  # Tiered: 1.5% of £100

def test_history_is_isolated():
    p = PaymentProcessor()
    p.process_payment(100.0, "GBP")
    history = p.get_transaction_history()
    history.clear()  # mutate the returned list
    assert len(p.get_transaction_history()) == 1  # original must be unaffected

if __name__ == "__main__":
    print("Running Payment Processor tests...")
    test_process_payment_returns_receipt()
    print("✓ test_process_payment_returns_receipt")
    test_transaction_history_grows()
    print("✓ test_transaction_history_grows")
    test_discount_reduces_amount()
    print("✓ test_discount_reduces_amount")
    test_fee_calculation()
    print("✓ test_fee_calculation")
    test_history_is_isolated()
    print("✓ test_history_is_isolated")
    print("\nAll Payment Processor tests passed! ✅")