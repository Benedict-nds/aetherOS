from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.medicine import Medicine
from app.models.medicine_category import MedicineCategory


def list_categories(db: Session) -> list[MedicineCategory]:
    return list(
        db.scalars(
            select(MedicineCategory).order_by(MedicineCategory.name.asc())
        ).all()
    )


def get_category_by_id(db: Session, category_id: int) -> MedicineCategory | None:
    return db.get(MedicineCategory, category_id)


def get_category_by_name(db: Session, name: str) -> MedicineCategory | None:
    return db.scalar(select(MedicineCategory).where(MedicineCategory.name == name))


def create_category(db: Session, category: MedicineCategory) -> MedicineCategory:
    db.add(category)
    db.flush()
    return category


def list_medicines(
    db: Session,
    *,
    q: str | None = None,
    category_id: int | None = None,
    is_active: bool | None = True,
) -> list[Medicine]:
    stmt = select(Medicine).options(joinedload(Medicine.category))

    if is_active is not None:
        stmt = stmt.where(Medicine.is_active.is_(is_active))

    if category_id is not None:
        stmt = stmt.where(Medicine.category_id == category_id)

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Medicine.name.ilike(pattern),
                Medicine.generic_name.ilike(pattern),
                Medicine.brand_name.ilike(pattern),
                Medicine.barcode.ilike(pattern),
            )
        )

    stmt = stmt.order_by(Medicine.name.asc())
    return list(db.scalars(stmt).unique().all())


def get_medicine_by_id(db: Session, medicine_id: int) -> Medicine | None:
    return db.scalar(
        select(Medicine)
        .options(joinedload(Medicine.category))
        .where(Medicine.id == medicine_id)
    )


def get_medicine_by_barcode(db: Session, barcode: str) -> Medicine | None:
    return db.scalar(select(Medicine).where(Medicine.barcode == barcode))


def create_medicine(db: Session, medicine: Medicine) -> Medicine:
    db.add(medicine)
    db.flush()
    return medicine


def update_medicine(db: Session, medicine: Medicine) -> Medicine:
    db.add(medicine)
    db.flush()
    return medicine


def get_batch_by_id(db: Session, batch_id: int) -> Batch | None:
    return db.get(Batch, batch_id)


def get_batch_by_medicine_and_number(
    db: Session,
    medicine_id: int,
    batch_number: str,
) -> Batch | None:
    return db.scalar(
        select(Batch).where(
            Batch.medicine_id == medicine_id,
            Batch.batch_number == batch_number,
        )
    )


def insert_batch(db: Session, batch: Batch) -> Batch:
    db.add(batch)
    db.flush()
    return batch


def list_batches_by_medicine(db: Session, medicine_id: int) -> list[Batch]:
    return list(
        db.scalars(
            select(Batch)
            .where(Batch.medicine_id == medicine_id)
            .order_by(Batch.expiry_date.asc().nulls_last(), Batch.id.asc())
        )
    )


def insert_inventory_movement(
    db: Session,
    movement: InventoryMovement,
) -> InventoryMovement:
    db.add(movement)
    db.flush()
    return movement


def sum_non_void_quantity(db: Session, medicine_id: int) -> int:
    total = db.scalar(
        select(func.coalesce(func.sum(Batch.quantity_on_hand), 0)).where(
            Batch.medicine_id == medicine_id,
            Batch.status != "void",
        )
    )
    return int(total or 0)


def fetch_inventory_movements(
    db: Session,
    *,
    limit: int,
    offset: int,
    medicine_id: int | None = None,
    batch_id: int | None = None,
) -> tuple[list[InventoryMovement], int]:
    filters = []

    if medicine_id is not None:
        filters.append(InventoryMovement.medicine_id == medicine_id)
    if batch_id is not None:
        filters.append(InventoryMovement.batch_id == batch_id)

    base_query = select(InventoryMovement)
    count_query = select(func.count()).select_from(InventoryMovement)

    if filters:
        base_query = base_query.where(*filters)
        count_query = count_query.where(*filters)

    total = db.scalar(count_query) or 0
    movements = db.scalars(
        base_query.order_by(
            InventoryMovement.created_at.desc(),
            InventoryMovement.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()

    return list(movements), total
