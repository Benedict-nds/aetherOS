from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MedicineCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    status: str = Field(default="active", max_length=20)


class MedicineCategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    generic_name: str | None = Field(default=None, max_length=200)
    brand_name: str | None = Field(default=None, max_length=200)
    category_id: int | None = None
    barcode: str | None = Field(default=None, max_length=100)
    dosage_form: str | None = Field(default=None, max_length=100)
    strength: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, max_length=50)
    reorder_level: int = Field(default=0, ge=0)
    is_active: bool = True


class MedicineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    generic_name: str | None = Field(default=None, max_length=200)
    brand_name: str | None = Field(default=None, max_length=200)
    category_id: int | None = None
    barcode: str | None = Field(default=None, max_length=100)
    dosage_form: str | None = Field(default=None, max_length=100)
    strength: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, max_length=50)
    reorder_level: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class MedicineResponse(BaseModel):
    id: int
    name: str
    generic_name: str | None
    brand_name: str | None
    category_id: int | None
    category_name: str | None = None
    barcode: str | None
    dosage_form: str | None
    strength: str | None
    unit: str | None
    reorder_level: int
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BatchCreate(BaseModel):
    medicine_id: int = Field(gt=0)
    batch_number: str = Field(min_length=1, max_length=100)
    expiry_date: date
    cost_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    selling_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    quantity_received: int = Field(gt=0)


class BatchResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    medicine_id: int
    supplier_id: int | None
    batch_number: str
    expiry_date: date | None
    cost_price: Decimal
    selling_price: Decimal
    quantity_on_hand: int
    quantity_received: int
    status: str
    created_at: datetime


class InventoryMovementResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    medicine_id: int
    batch_id: int | None
    movement_type: str
    quantity_change: int
    reference_type: str | None
    reference_id: int | None
    user_id: int
    created_at: datetime


class InventoryMovementListResponse(BaseModel):
    items: list[InventoryMovementResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
