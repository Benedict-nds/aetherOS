from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

PaymentMethod = Literal["cash", "momo", "card"]


class SaleLineCreate(BaseModel):
    medicine_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    payment_method: PaymentMethod
    lines: list[SaleLineCreate] = Field(min_length=1)

    @field_validator("lines")
    @classmethod
    def lines_not_empty(cls, value: list[SaleLineCreate]) -> list[SaleLineCreate]:
        if not value:
            raise ValueError("At least one line is required")
        return value


class SaleLineResponse(BaseModel):
    id: int
    batch_id: int
    medicine_id: int
    quantity: int
    unit_price: Decimal

    model_config = {"from_attributes": True}


class SaleResponse(BaseModel):
    id: int
    payment_method: str
    total: Decimal
    user_id: int
    lines: list[SaleLineResponse]
    created_at: str
