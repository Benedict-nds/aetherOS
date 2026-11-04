from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

RefundMethod = Literal["cash", "momo", "card"]


class RefundLineCreate(BaseModel):
    sale_line_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    return_to_stock: bool


class RefundCreate(BaseModel):
    sale_id: int = Field(gt=0)
    reason: str = Field(min_length=3)
    refund_method: RefundMethod
    lines: list[RefundLineCreate] = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 3:
            raise ValueError("Reason must be at least 3 characters")
        return trimmed

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, value: list[RefundLineCreate]) -> list[RefundLineCreate]:
        if not value:
            raise ValueError("At least one line is required")
        return value


class RefundLineResponse(BaseModel):
    sale_line_id: int
    medicine_id: int
    medicine_name: str
    batch_id: int
    quantity: int
    amount: Decimal
    return_to_stock: bool


class RefundResponse(BaseModel):
    id: int
    refund_number: str
    sale_id: int
    reason: str
    refund_method: str
    total_amount: Decimal
    created_at: str
    cashier: dict
    lines: list[RefundLineResponse]
