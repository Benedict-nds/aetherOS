from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.refund import Refund
from app.models.refund_item import RefundItem
from app.models.sale import Sale
from app.models.sale_line import SaleLine


def get_sale_for_refund(db: Session, sale_id: int) -> Sale | None:
    result = db.execute(
        select(Sale)
        .options(
            joinedload(Sale.user),
            joinedload(Sale.lines).joinedload(SaleLine.batch),
            joinedload(Sale.lines).joinedload(SaleLine.medicine),
        )
        .where(Sale.id == sale_id)
    )
    return result.unique().scalar_one_or_none()


def get_sale_lines_for_update(
    db: Session,
    *,
    sale_id: int,
    line_ids: list[int],
) -> list[SaleLine]:
    if not line_ids:
        return []
    stmt = (
        select(SaleLine)
        .options(
            joinedload(SaleLine.batch),
            joinedload(SaleLine.medicine),
        )
        .where(
            SaleLine.sale_id == sale_id,
            SaleLine.id.in_(line_ids),
        )
        .with_for_update()
    )
    return list(db.scalars(stmt).unique().all())


def get_refunded_quantities_by_sale_line(
    db: Session,
    *,
    sale_line_ids: list[int],
) -> dict[int, int]:
    if not sale_line_ids:
        return {}
    rows = db.execute(
        select(RefundItem.sale_line_id, func.coalesce(func.sum(RefundItem.quantity), 0))
        .where(RefundItem.sale_line_id.in_(sale_line_ids))
        .group_by(RefundItem.sale_line_id)
    ).all()
    return {sale_line_id: int(total) for sale_line_id, total in rows}


def insert_refund(db: Session, refund: Refund) -> Refund:
    db.add(refund)
    db.flush()
    return refund


def insert_refund_item(db: Session, item: RefundItem) -> RefundItem:
    db.add(item)
    db.flush()
    return item


def get_refund(db: Session, refund_id: int) -> Refund | None:
    result = db.execute(
        select(Refund)
        .options(
            joinedload(Refund.user),
            joinedload(Refund.items)
            .joinedload(RefundItem.sale_line)
            .joinedload(SaleLine.batch),
            joinedload(Refund.items)
            .joinedload(RefundItem.sale_line)
            .joinedload(SaleLine.medicine),
        )
        .where(Refund.id == refund_id)
    )
    return result.unique().scalar_one_or_none()
