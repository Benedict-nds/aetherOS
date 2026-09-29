from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.sale import Sale
from app.models.sale_line import SaleLine
from app.modules.inventory.repository import get_medicine_by_id


def fetch_fefo_batches_for_update(
    db: Session,
    *,
    medicine_id: int,
    as_of: date,
) -> list[Batch]:
    """Sellable batches for a medicine, FEFO order, row-locked for update."""
    stmt = (
        select(Batch)
        .where(
            Batch.medicine_id == medicine_id,
            Batch.status != "void",
            Batch.quantity_on_hand > 0,
            (Batch.expiry_date.is_(None)) | (Batch.expiry_date >= as_of),
        )
        .order_by(Batch.expiry_date.asc().nulls_last(), Batch.id.asc())
        .with_for_update()
    )
    return list(db.scalars(stmt))


def insert_sale(db: Session, sale: Sale) -> Sale:
    db.add(sale)
    db.flush()
    return sale


def insert_sale_line(db: Session, line: SaleLine) -> SaleLine:
    db.add(line)
    db.flush()
    return line


def medicine_exists(db: Session, medicine_id: int) -> bool:
    return get_medicine_by_id(db, medicine_id) is not None


def sum_sales_total_for_utc_day(db: Session, *, day: date) -> Decimal:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    total = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.created_at >= start,
            Sale.created_at < end,
        )
    )
    return Decimal(str(total or 0))
