"""Payment processor with tiered fees, regional tax and an append-only audit trail.

All money uses Decimal (never float), and every record is a frozen dataclass,
so nothing stored by the processor can be changed after it is created.
The fee tiers and tax rates are simplified example values, not real regulation.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

CENT = Decimal("0.01")


class CurrencyRegion(Enum):
    UK = "UK"
    US = "US"
    EU = "EU"
    CRYPTO = "CRYPTO"


CURRENCY_REGIONS = {
    "GBP": CurrencyRegion.UK,
    "USD": CurrencyRegion.US,
    "EUR": CurrencyRegion.EU,
    "BTC": CurrencyRegion.CRYPTO,
    "ETH": CurrencyRegion.CRYPTO,
}

# Example tax rate per region (illustrative values only)
REGIONAL_TAX_RATES = {
    CurrencyRegion.UK: Decimal("0"),
    CurrencyRegion.US: Decimal("0"),
    CurrencyRegion.EU: Decimal("0.15"),
    CurrencyRegion.CRYPTO: Decimal("0"),
}

# Marginal fee tiers, like tax brackets: (upper limit of the tier, rate).
# A payment of 2,000 pays 1.5% on the first 1,000 and 1.2% on the next 1,000,
# so a slightly larger payment never gets a smaller fee.
FEE_TIERS = [
    (Decimal("1000"), Decimal("0.015")),
    (Decimal("5000"), Decimal("0.012")),
    (None, Decimal("0.010")),  # everything above 5,000
]

DISCOUNT_CODES = {"SAVE10": Decimal("0.10")}


def to_money(amount: Decimal) -> Decimal:
    """Rounds to whole cents."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class AuditEvent:
    action: str
    timestamp: datetime
    details: str


@dataclass(frozen=True)
class Receipt:
    transaction_id: str
    amount: Decimal
    currency: str
    region: CurrencyRegion
    timestamp: datetime
    fee: Decimal
    tax: Decimal

    @property
    def total(self) -> Decimal:
        return to_money(self.amount + self.fee + self.tax)


class PaymentProcessor:
    def __init__(self):
        self._history: list[Receipt] = []
        self._audit_trail: list[AuditEvent] = []

    @staticmethod
    def _region(currency: str) -> CurrencyRegion:
        try:
            return CURRENCY_REGIONS[currency]
        except KeyError:
            raise ValueError(f"Unsupported currency: {currency}") from None

    @staticmethod
    def calculate_fee(amount: Decimal) -> Decimal:
        """Marginal tiered fee: each part of the amount pays its own tier's rate."""
        amount = Decimal(amount)
        fee = Decimal("0")
        lower = Decimal("0")
        for upper, rate in FEE_TIERS:
            if upper is None or amount <= upper:
                fee += (amount - lower) * rate
                break
            fee += (upper - lower) * rate
            lower = upper
        return to_money(fee)

    def calculate_tax(self, amount: Decimal, currency: str) -> Decimal:
        rate = REGIONAL_TAX_RATES[self._region(currency)]
        return to_money(Decimal(amount) * rate)

    def process_payment(self, amount, currency: str) -> Receipt:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        region = self._region(currency)  # raises for unsupported currencies

        now = datetime.now(timezone.utc)
        receipt = Receipt(
            transaction_id=str(uuid.uuid4()),
            amount=to_money(amount),
            currency=currency,
            region=region,
            timestamp=now,
            fee=self.calculate_fee(amount),
            tax=self.calculate_tax(amount, currency),
        )
        self._history.append(receipt)
        self._audit_trail.append(AuditEvent(
            action="payment_processed",
            timestamp=now,
            details=(f"Transaction {receipt.transaction_id}: {receipt.amount} {currency}, "
                     f"fee={receipt.fee}, tax={receipt.tax}"),
        ))
        return receipt

    @staticmethod
    def apply_discount(code: str, amount) -> Decimal:
        """Returns the discounted amount; unknown codes leave it unchanged."""
        amount = Decimal(str(amount))
        rate = DISCOUNT_CODES.get(code, Decimal("0"))
        return to_money(amount * (1 - rate))

    def get_transaction_history(self) -> tuple[Receipt, ...]:
        # A tuple of frozen receipts: callers can read the history but not change it
        return tuple(self._history)

    def audit_trail(self) -> tuple[AuditEvent, ...]:
        return tuple(self._audit_trail)


if __name__ == "__main__":
    processor = PaymentProcessor()
    for amount, currency in [("100.00", "GBP"), ("2000.00", "EUR"), ("7500.00", "USD")]:
        r = processor.process_payment(amount, currency)
        print(f"{r.amount} {r.currency}: fee {r.fee}, tax {r.tax}, total {r.total}")
