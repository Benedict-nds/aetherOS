from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ReceiptLine(BaseModel):
    medicine_id: int = Field(gt=0)
    batch_number: str = Field(min_length=1, max_length=100)
    expiry_date: date | None = None
    cost_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    selling_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    quantity_received: int = Field(gt=0)


class ReceiptCreate(BaseModel):
    supplier_id: int = Field(gt=0)
    lines: list[ReceiptLine] = Field(min_length=1)
