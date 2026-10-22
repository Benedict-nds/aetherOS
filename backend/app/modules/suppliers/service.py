from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.models.user import User
from app.modules.audit.service import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE, create_audit_log
from app.modules.suppliers import repository
from app.modules.suppliers.schemas import SupplierCreate, SupplierListResponse, SupplierResponse, SupplierUpdate

ENTITY_TYPE_SUPPLIER = "supplier"


def _serialize(supplier: Supplier) -> dict:
    return SupplierResponse.model_validate(supplier).model_dump(mode="json")


def list_supplier_records(db: Session, *, q: str | None, is_active: bool | None, limit: int, offset: int) -> dict:
    items, total = repository.list_suppliers(db, q=q, is_active=is_active, limit=limit, offset=offset)
    return SupplierListResponse(items=[SupplierResponse.model_validate(x) for x in items], total=total, limit=limit, offset=offset).model_dump(mode="json")


def get_supplier_record(db: Session, supplier_id: int) -> dict | None:
    supplier = repository.get_supplier(db, supplier_id)
    return _serialize(supplier) if supplier else None


def _audit(db: Session, actor: User, action: str, supplier: Supplier, ip_address: str | None) -> None:
    create_audit_log(db, user=actor, action=action, entity_type=ENTITY_TYPE_SUPPLIER,
                     entity_id=supplier.id, details={"name": supplier.name}, ip_address=ip_address)


def create_supplier_record(db: Session, actor: User, payload: SupplierCreate, *, ip_address: str | None = None) -> dict:
    if repository.get_supplier_by_name(db, payload.name):
        raise HTTPException(status_code=409, detail="Supplier name already exists")
    supplier = Supplier(**payload.model_dump())
    try:
        repository.save_supplier(db, supplier)
        _audit(db, actor, ACTION_CREATE, supplier, ip_address)
        db.commit()
        db.refresh(supplier)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Supplier name already exists") from exc
    return _serialize(supplier)


def update_supplier_record(db: Session, actor: User, supplier_id: int, payload: SupplierUpdate, *, ip_address: str | None = None) -> dict:
    supplier = repository.get_supplier(db, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    updates = payload.model_dump(exclude_unset=True)
    new_name = updates.get("name")
    if new_name is not None:
        existing = repository.get_supplier_by_name(db, new_name)
        if existing is not None and existing.id != supplier.id:
            raise HTTPException(status_code=409, detail="Supplier name already exists")
    for key, value in updates.items():
        setattr(supplier, key, str(value) if key == "email" and value is not None else value)
    try:
        repository.update_supplier(db, supplier)
        _audit(db, actor, ACTION_UPDATE, supplier, ip_address)
        db.commit()
        db.refresh(supplier)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Supplier name already exists") from exc
    return _serialize(supplier)


def deactivate_supplier_record(db: Session, actor: User, supplier_id: int, *, ip_address: str | None = None) -> None:
    supplier = repository.get_supplier(db, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.is_active = False
    try:
        repository.update_supplier(db, supplier)
        _audit(db, actor, ACTION_DELETE, supplier, ip_address)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Supplier could not be deactivated") from exc
