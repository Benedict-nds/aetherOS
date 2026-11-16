from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.batch import Batch
from app.models.medicine import Medicine
from app.models.medicine_category import MedicineCategory
from app.models.sale import Sale
from app.models.sale_line import SaleLine
from app.models.user import User

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


def fetch_daily_sales(db: Session, *, day: date) -> dict:
    # Same half-open UTC interval as the dashboard; sales have no status column.
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    filters = (Sale.created_at >= start, Sale.created_at < end)
    total = db.execute(
        select(func.coalesce(func.sum(Sale.total), 0).label("total_amount"),
               func.count(Sale.id).label("sale_count")).where(*filters)
    ).mappings().one()
    payments = db.execute(
        select(Sale.payment_method, func.count(Sale.id).label("sale_count"),
               func.sum(Sale.total).label("amount"))
        .where(*filters).group_by(Sale.payment_method).order_by(Sale.payment_method)
    ).mappings().all()
    cashiers = db.execute(
        select(User.id.label("user_id"), User.full_name,
               func.count(Sale.id).label("sale_count"), func.sum(Sale.total).label("amount"))
        .select_from(Sale).join(User, Sale.user_id == User.id).where(*filters)
        .group_by(User.id, User.full_name).order_by(User.id)
    ).mappings().all()
    categories = db.execute(
        select(MedicineCategory.id.label("category_id"),
               MedicineCategory.name.label("category_name"),
               func.sum(SaleLine.quantity).label("quantity"),
               func.sum(SaleLine.quantity * SaleLine.unit_price).label("amount"))
        .select_from(SaleLine).join(Sale, SaleLine.sale_id == Sale.id)
        .join(Medicine, SaleLine.medicine_id == Medicine.id)
        .outerjoin(MedicineCategory, Medicine.category_id == MedicineCategory.id)
        .where(*filters).group_by(MedicineCategory.id, MedicineCategory.name)
        .order_by(MedicineCategory.id.asc().nulls_last())
    ).mappings().all()
    return dict(total, by_payment_method=payments, by_cashier=cashiers, by_category=categories)


def fetch_inventory_valuation_rows(db: Session):
    cost_value = func.sum(Batch.quantity_on_hand * Batch.cost_price).label("cost_value")
    return db.execute(
        select(Medicine.id.label("medicine_id"), Medicine.name,
               MedicineCategory.name.label("category_name"),
               func.sum(Batch.quantity_on_hand).label("quantity_on_hand"), cost_value,
               func.sum(Batch.quantity_on_hand * Batch.selling_price).label("retail_value"))
        .select_from(Batch).join(Medicine, Batch.medicine_id == Medicine.id)
        .outerjoin(MedicineCategory, Medicine.category_id == MedicineCategory.id)
        .where(Batch.status != VOID_STATUS, Batch.quantity_on_hand > 0)
        .group_by(Medicine.id, Medicine.name, MedicineCategory.id, MedicineCategory.name)
        .order_by(cost_value.desc(), Medicine.id.asc())
    ).mappings().all()
