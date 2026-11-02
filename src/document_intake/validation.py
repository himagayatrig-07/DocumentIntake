"""Business-rule checks on an extracted invoice.

These return a list of issues instead of raising: any issue means the document
goes to the human review queue rather than being saved automatically.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from document_intake.models import Invoice

# Allow one cent of rounding per value being combined.
CENT = Decimal("0.01")


@dataclass(frozen=True)
class Issue:
    field: str
    code: str
    message: str


def validate_invoice(invoice: Invoice, today: date | None = None) -> list[Issue]:
    today = today or date.today()
    issues: list[Issue] = []

    for name in ("subtotal", "tax", "total"):
        if getattr(invoice, name) < 0:
            issues.append(Issue(name, "negative_amount", f"{name} is negative"))

    for i, item in enumerate(invoice.line_items):
        expected = item.quantity * item.unit_price
        if abs(expected - item.amount) > CENT:
            issues.append(
                Issue(
                    f"line_items[{i}].amount",
                    "line_amount_mismatch",
                    f"quantity x unit_price = {expected}, but amount is {item.amount}",
                )
            )

    if invoice.line_items:
        line_sum = sum((item.amount for item in invoice.line_items), Decimal(0))
        if abs(line_sum - invoice.subtotal) > CENT * len(invoice.line_items):
            issues.append(
                Issue(
                    "subtotal",
                    "subtotal_mismatch",
                    f"line items sum to {line_sum}, but subtotal is {invoice.subtotal}",
                )
            )

    if abs(invoice.subtotal + invoice.tax - invoice.total) > CENT:
        issues.append(
            Issue(
                "total",
                "total_mismatch",
                f"subtotal + tax = {invoice.subtotal + invoice.tax}, but total is {invoice.total}",
            )
        )

    if invoice.invoice_date > today:
        issues.append(Issue("invoice_date", "future_date", "invoice date is in the future"))

    if invoice.due_date is not None and invoice.due_date < invoice.invoice_date:
        issues.append(Issue("due_date", "due_before_invoice", "due date is before invoice date"))

    return issues
