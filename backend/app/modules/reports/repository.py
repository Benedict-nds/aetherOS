from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.batch import Batch
from app.models.medicine import Medicine

VOID_STATUS = "void"


def _batch_quantity_subquery():
    return (
        select(
            Batch.medicine_id.label("medicine_id"),
            func.coalesce(func.sum(Batch.quantity_on_hand), 0).label("quantity_on_hand"),
        )
        .where(Batch.status != VOID_STATUS)
        .group_by(Batch.medicine_id)
        .subquery()
    )


def fetch_low_stock_rows(db: Session) -> list[tuple[Medicine, int]]:
    quantities = _batch_quantity_subquery()

    quantity_on_hand = func.coalesce(quantities.c.quantity_on_hand, 0)

    stmt = (
        select(Medicine, quantity_on_hand.label("quantity_on_hand"))
        .outerjoin(quantities, Medicine.id == quantities.c.medicine_id)
        .options(joinedload(Medicine.category))
        .where(quantity_on_hand <= Medicine.reorder_level)
        .order_by(quantity_on_hand.asc(), Medicine.name.asc())
    )

    return list(db.execute(stmt).all())


def fetch_expiry_batches(db: Session, *, within_days: int) -> list[tuple[Batch, Medicine]]:
    today = date.today()
    cutoff = today + timedelta(days=within_days)

    stmt = (
        select(Batch, Medicine)
        .join(Medicine, Batch.medicine_id == Medicine.id)
        .where(
            Batch.expiry_date.isnot(None),
            Batch.expiry_date <= cutoff,
            Batch.status != VOID_STATUS,
        )
        .order_by(Batch.expiry_date.asc(), Batch.id.asc())
    )

    return list(db.execute(stmt).all())
