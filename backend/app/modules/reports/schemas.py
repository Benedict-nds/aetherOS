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
