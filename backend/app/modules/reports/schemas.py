from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class LowStockReportRow(BaseModel):
    medicine_id: int
    name: str
    category_name: str | None
    quantity_on_hand: int = Field(ge=0)
    reorder_level: int = Field(ge=0)


class ExpiryReportRow(BaseModel):
    medicine_id: int
    name: str
    batch_id: int
    batch_number: str
    expiry_date: str
    quantity_on_hand: int = Field(ge=0)
    bucket: str


class PaymentMethodSales(BaseModel):
    payment_method: str
    sale_count: int
    amount: Decimal


class CashierSales(BaseModel):
    user_id: int
    full_name: str
    sale_count: int
    amount: Decimal


class CategorySales(BaseModel):
    category_id: int | None
    category_name: str | None
    quantity: int
    amount: Decimal


class DailySalesReport(BaseModel):
    date: date
    currency: str = "GHS"
    total_amount: Decimal
    sale_count: int
    by_payment_method: list[PaymentMethodSales]
    by_cashier: list[CashierSales]
    by_category: list[CategorySales]


class InventoryValuationRow(BaseModel):
    medicine_id: int
    name: str
    category_name: str | None
    quantity_on_hand: int
    cost_value: Decimal
    retail_value: Decimal


class InventoryValuationReport(BaseModel):
    currency: str = "GHS"
    total_cost_value: Decimal
    total_retail_value: Decimal
    rows: list[InventoryValuationRow]
