"""Invoice schema: the structured fields the extractor must produce.

Money is stored as Decimal, never float, so totals can be checked exactly.
Type and format checks live here; cross-field business rules live in validation.py,
because a rule failure should send a document to human review, not raise an error.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class Invoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vendor_name: str = Field(min_length=1)
    invoice_number: str = Field(min_length=1)
    invoice_date: date
    due_date: date | None = None
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO 4217 code, e.g. USD")
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    line_items: list[LineItem] = Field(default_factory=list)
