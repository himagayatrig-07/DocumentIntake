from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from document_intake.models import Invoice
from document_intake.validation import validate_invoice

TODAY = date(2026, 11, 2)


def make_invoice(**overrides) -> Invoice:
    data = {
        "vendor_name": "Acme Supplies",
        "invoice_number": "INV-1001",
        "invoice_date": "2026-10-15",
        "due_date": "2026-11-14",
        "currency": "USD",
        "subtotal": "150.00",
        "tax": "12.00",
        "total": "162.00",
        "line_items": [
            {"description": "Paper", "quantity": "10", "unit_price": "5.00", "amount": "50.00"},
            {"description": "Toner", "quantity": "2", "unit_price": "50.00", "amount": "100.00"},
        ],
    }
    data.update(overrides)
    return Invoice.model_validate(data)


def codes(invoice: Invoice) -> set[str]:
    return {issue.code for issue in validate_invoice(invoice, today=TODAY)}


def test_valid_invoice_has_no_issues():
    assert codes(make_invoice()) == set()


def test_money_is_decimal():
    assert make_invoice().total == Decimal("162.00")


def test_total_mismatch():
    assert codes(make_invoice(total="170.00")) == {"total_mismatch"}


def test_subtotal_mismatch():
    assert "subtotal_mismatch" in codes(make_invoice(subtotal="140.00", total="152.00"))


def test_line_amount_mismatch():
    items = [
        {"description": "Paper", "quantity": "10", "unit_price": "5.00", "amount": "55.00"},
        {"description": "Toner", "quantity": "2", "unit_price": "50.00", "amount": "95.00"},
    ]
    assert codes(make_invoice(line_items=items)) == {"line_amount_mismatch"}


def test_rounding_within_a_cent_is_accepted():
    items = [{"description": "Widget", "quantity": "3", "unit_price": "0.333", "amount": "1.00"}]
    assert codes(make_invoice(line_items=items, subtotal="1.00", tax="0", total="1.00")) == set()


def test_due_before_invoice_date():
    assert codes(make_invoice(due_date="2026-10-01")) == {"due_before_invoice"}


def test_future_invoice_date():
    assert "future_date" in codes(make_invoice(invoice_date="2026-12-01", due_date=None))


def test_negative_amount():
    assert "negative_amount" in codes(make_invoice(tax="-1.00", total="149.00"))


def test_invoice_without_line_items_skips_line_checks():
    assert codes(make_invoice(line_items=[])) == set()


@pytest.mark.parametrize(
    "overrides",
    [
        {"currency": "usd"},
        {"invoice_date": "not a date"},
        {"total": "abc"},
        {"vendor_name": ""},
        {"unexpected_field": "x"},
    ],
)
def test_schema_rejects_bad_values(overrides):
    with pytest.raises(ValidationError):
        make_invoice(**overrides)
