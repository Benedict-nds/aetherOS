from pydantic import BaseModel, Field


class TodaySalesSummary(BaseModel):
    amount: float = Field(ge=0)
    currency: str = "GHS"


class DashboardSummary(BaseModel):
    today_sales: TodaySalesSummary
    low_stock_count: int = Field(ge=0)
    expiring_soon_count: int = Field(ge=0)
    open_orders_count: int = Field(ge=0)
