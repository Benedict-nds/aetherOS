from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

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
