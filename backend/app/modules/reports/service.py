from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.reports import repository
from app.modules.reports.schemas import (
    DailySalesReport, ExpiryReportRow, InventoryValuationReport,
    InventoryValuationRow, LowStockReportRow,
)

def expiry_bucket(expiry_date: date, *, today: date | None = None) -> str:
    today = today or date.today()

    if expiry_date < today:
        return "expired"
    if expiry_date <= today + timedelta(days=30):
        return "30"
    if expiry_date <= today + timedelta(days=60):
        return "60"
    return "90"


def get_low_stock_report(db: Session) -> list[dict]:
    rows = repository.fetch_low_stock_rows(db)
    return [
        LowStockReportRow(
            medicine_id=medicine.id,
            name=medicine.name,
            category_name=medicine.category.name if medicine.category else None,
            quantity_on_hand=quantity_on_hand,
            reorder_level=medicine.reorder_level,
        ).model_dump()
        for medicine, quantity_on_hand in rows
    ]


def get_expiry_report(db: Session, *, within_days: int = 90) -> list[dict]:
    rows = repository.fetch_expiry_batches(db, within_days=within_days)
    return [
        ExpiryReportRow(
            medicine_id=medicine.id,
            name=medicine.name,
            batch_id=batch.id,
            batch_number=batch.batch_number,
            expiry_date=batch.expiry_date.isoformat(),
            quantity_on_hand=batch.quantity_on_hand,
            bucket=expiry_bucket(batch.expiry_date),
        ).model_dump()
        for batch, medicine in rows
        if batch.expiry_date is not None
    ]


def count_expiring_soon(db: Session) -> int:
    rows = get_expiry_report(db, within_days=30)
    return sum(1 for row in rows if row["bucket"] in {"expired", "30"})


def get_daily_sales_report(db: Session, *, day: date | None = None) -> dict:
    day = day if day is not None else datetime.now(timezone.utc).date()
    return DailySalesReport(date=day, **repository.fetch_daily_sales(db, day=day)).model_dump()


def get_inventory_valuation_report(db: Session) -> dict:
    rows = [InventoryValuationRow(**row) for row in repository.fetch_inventory_valuation_rows(db)]
    return InventoryValuationReport(
        total_cost_value=sum((row.cost_value for row in rows), Decimal("0.00")),
        total_retail_value=sum((row.retail_value for row in rows), Decimal("0.00")),
        rows=rows,
    ).model_dump()
