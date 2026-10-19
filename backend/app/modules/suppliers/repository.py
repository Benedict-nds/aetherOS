from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.supplier import Supplier


def list_suppliers(
    db: Session, *, q: str | None, is_active: bool | None, limit: int, offset: int
) -> tuple[list[Supplier], int]:
    filters = []
    if is_active is not None:
        filters.append(Supplier.is_active.is_(is_active))
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        filters.append(or_(
            Supplier.name.ilike(pattern), Supplier.phone.ilike(pattern),
            Supplier.email.ilike(pattern), Supplier.contact_person.ilike(pattern),
        ))
    base = select(Supplier)
    count = select(func.count()).select_from(Supplier)
    if filters:
        base, count = base.where(*filters), count.where(*filters)
    total = db.scalar(count) or 0
    items = db.scalars(base.order_by(Supplier.name.asc(), Supplier.id.asc()).limit(limit).offset(offset)).all()
    return list(items), total


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    return db.get(Supplier, supplier_id)


def get_supplier_by_name(db: Session, name: str) -> Supplier | None:
    return db.scalar(select(Supplier).where(func.lower(Supplier.name) == name.lower()))


def save_supplier(db: Session, supplier: Supplier) -> Supplier:
    db.add(supplier)
    db.flush()
    return supplier


def update_supplier(db: Session, supplier: Supplier) -> Supplier:
    db.flush()
    return supplier
