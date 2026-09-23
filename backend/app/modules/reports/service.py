from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.modules.reports import repository
from app.modules.reports.schemas import ExpiryReportRow, LowStockReportRow

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
