from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.medicine import Medicine
from app.models.medicine_category import MedicineCategory
from app.models.user import User
from app.modules.audit.service import (
    ACTION_CREATE,
    ACTION_UPDATE,
    ENTITY_TYPE_BATCH,
    ENTITY_TYPE_MEDICINE,
    create_audit_log,
)
from app.modules.inventory import repository
from app.modules.inventory.repository import insert_inventory_movement
from app.modules.inventory.schemas import (
    BatchCreate,
    BatchResponse,
    InventoryMovementListResponse,
    InventoryMovementResponse,
    MedicineCategoryCreate,
    MedicineCategoryResponse,
    MedicineCreate,
    MedicineResponse,
    MedicineUpdate,
)

MOVEMENT_TYPE_STOCK_IN = "stock_in"
REFERENCE_TYPE_BATCH = "batch"
BATCH_STATUS_ACTIVE = "active"
BATCH_STATUS_EXPIRED = "expired"


def serialize_category(category: MedicineCategory) -> dict:
    return MedicineCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        status=category.status,
        created_at=category.created_at.isoformat(),
    ).model_dump()


def serialize_medicine(medicine: Medicine) -> dict:
    return MedicineResponse(
        id=medicine.id,
        name=medicine.name,
        generic_name=medicine.generic_name,
        brand_name=medicine.brand_name,
        category_id=medicine.category_id,
        category_name=medicine.category.name if medicine.category else None,
        barcode=medicine.barcode,
        dosage_form=medicine.dosage_form,
        strength=medicine.strength,
        unit=medicine.unit,
        reorder_level=medicine.reorder_level,
        is_active=medicine.is_active,
        created_at=medicine.created_at.isoformat(),
        updated_at=medicine.updated_at.isoformat(),
    ).model_dump()


def serialize_batch(batch: Batch) -> dict:
    return BatchResponse.model_validate(batch).model_dump(mode="json")


def _audit_medicine_details(medicine: Medicine) -> dict:
    return {
        "name": medicine.name,
        "generic_name": medicine.generic_name,
        "brand_name": medicine.brand_name,
        "category_id": medicine.category_id,
        "barcode": medicine.barcode,
        "is_active": medicine.is_active,
    }


def _validate_category_id(db: Session, category_id: int | None) -> None:
    if category_id is None:
        return

    category = repository.get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unknown category_id",
        )


def list_category_records(db: Session) -> list[dict]:
    categories = repository.list_categories(db)
    return [serialize_category(category) for category in categories]


def create_category_record(
    db: Session,
    payload: MedicineCategoryCreate,
) -> dict:
    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category name is required",
        )

    existing = repository.get_category_by_name(db, name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        )

    category = MedicineCategory(
        name=name,
        description=payload.description,
        status=payload.status,
    )

    try:
        created = repository.create_category(db, category)
        db.commit()
        db.refresh(created)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        ) from exc

    return serialize_category(created)


def list_medicine_records(
    db: Session,
    *,
    q: str | None = None,
    category_id: int | None = None,
    is_active: bool | None = True,
) -> list[dict]:
    medicines = repository.list_medicines(
        db,
        q=q,
        category_id=category_id,
        is_active=is_active,
    )
    return [serialize_medicine(medicine) for medicine in medicines]


def get_medicine_record(db: Session, medicine_id: int) -> dict | None:
    medicine = repository.get_medicine_by_id(db, medicine_id)
    if medicine is None:
        return None
    data = serialize_medicine(medicine)
    data["quantity_on_hand"] = repository.sum_non_void_quantity(db, medicine.id)
    return data


def create_medicine_record(
    db: Session,
    actor: User,
    payload: MedicineCreate,
    *,
    ip_address: str | None = None,
) -> dict:
    _validate_category_id(db, payload.category_id)

    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Medicine name is required",
        )

    if payload.barcode:
        existing = repository.get_medicine_by_barcode(db, payload.barcode.strip())
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Barcode already exists",
            )

    medicine = Medicine(
        name=name,
        generic_name=payload.generic_name,
        brand_name=payload.brand_name,
        category_id=payload.category_id,
        barcode=payload.barcode.strip() if payload.barcode else None,
        dosage_form=payload.dosage_form,
        strength=payload.strength,
        unit=payload.unit,
        reorder_level=payload.reorder_level,
        is_active=payload.is_active,
    )

    try:
        created = repository.create_medicine(db, medicine)
        create_audit_log(
            db,
            action=ACTION_CREATE,
            entity_type=ENTITY_TYPE_MEDICINE,
            user=actor,
            entity_id=created.id,
            details=_audit_medicine_details(created),
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(created)
        created = repository.get_medicine_by_id(db, created.id)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Barcode already exists",
        ) from exc

    assert created is not None
    return serialize_medicine(created)


def update_medicine_record(
    db: Session,
    actor: User,
    medicine_id: int,
    payload: MedicineUpdate,
    *,
    ip_address: str | None = None,
) -> dict:
    medicine = repository.get_medicine_by_id(db, medicine_id)
    if medicine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    updates = payload.model_dump(exclude_unset=True)

    if "category_id" in updates:
        _validate_category_id(db, updates["category_id"])

    if "name" in updates:
        name = updates["name"].strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Medicine name is required",
            )
        medicine.name = name

    if "generic_name" in updates:
        medicine.generic_name = updates["generic_name"]
    if "brand_name" in updates:
        medicine.brand_name = updates["brand_name"]
    if "category_id" in updates:
        medicine.category_id = updates["category_id"]
    if "barcode" in updates:
        barcode = updates["barcode"].strip() if updates["barcode"] else None
        if barcode and barcode != medicine.barcode:
            existing = repository.get_medicine_by_barcode(db, barcode)
            if existing is not None and existing.id != medicine.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Barcode already exists",
                )
        medicine.barcode = barcode
    if "dosage_form" in updates:
        medicine.dosage_form = updates["dosage_form"]
    if "strength" in updates:
        medicine.strength = updates["strength"]
    if "unit" in updates:
        medicine.unit = updates["unit"]
    if "reorder_level" in updates:
        medicine.reorder_level = updates["reorder_level"]
    if "is_active" in updates:
        medicine.is_active = updates["is_active"]

    medicine.updated_at = datetime.now(timezone.utc)

    try:
        repository.update_medicine(db, medicine)
        create_audit_log(
            db,
            action=ACTION_UPDATE,
            entity_type=ENTITY_TYPE_MEDICINE,
            user=actor,
            entity_id=medicine.id,
            details=_audit_medicine_details(medicine),
            ip_address=ip_address,
        )
        db.commit()
        refreshed = repository.get_medicine_by_id(db, medicine.id)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Barcode already exists",
        ) from exc

    assert refreshed is not None
    return serialize_medicine(refreshed)


def _batch_status_for_expiry(expiry_date: date | None) -> str:
    if expiry_date is None:
        return BATCH_STATUS_ACTIVE
    today = datetime.now(timezone.utc).date()
    if expiry_date < today:
        return BATCH_STATUS_EXPIRED
    return BATCH_STATUS_ACTIVE


def apply_quantity_change(batch: Batch, quantity_change: int) -> int:
    """Apply a signed quantity change. Never allow quantity_on_hand to go negative."""
    resulting = batch.quantity_on_hand + quantity_change
    if resulting < 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient batch quantity",
        )
    batch.quantity_on_hand = resulting
    return resulting


def list_batches_for_medicine(db: Session, medicine_id: int) -> list[dict]:
    medicine = repository.get_medicine_by_id(db, medicine_id)
    if medicine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )
    batches = repository.list_batches_by_medicine(db, medicine_id)
    return [serialize_batch(batch) for batch in batches]


def create_batch_record(
    db: Session,
    actor: User,
    payload: BatchCreate,
    *,
    ip_address: str | None = None,
) -> dict:
    medicine = repository.get_medicine_by_id(db, payload.medicine_id)
    if medicine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    batch_number = payload.batch_number.strip()
    if not batch_number:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Batch number is required",
        )

    existing = repository.get_batch_by_medicine_and_number(
        db,
        payload.medicine_id,
        batch_number,
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch number already exists for this medicine",
        )

    batch = Batch(
        medicine_id=payload.medicine_id,
        batch_number=batch_number,
        expiry_date=payload.expiry_date,
        cost_price=payload.cost_price,
        selling_price=payload.selling_price,
        quantity_on_hand=0,
        quantity_received=payload.quantity_received,
        status=_batch_status_for_expiry(payload.expiry_date),
        supplier_id=None,
    )

    try:
        saved = repository.insert_batch(db, batch)
        apply_quantity_change(saved, payload.quantity_received)

        insert_inventory_movement(
            db,
            InventoryMovement(
                medicine_id=saved.medicine_id,
                batch_id=saved.id,
                movement_type=MOVEMENT_TYPE_STOCK_IN,
                quantity_change=payload.quantity_received,
                reference_type=REFERENCE_TYPE_BATCH,
                reference_id=saved.id,
                user_id=actor.id,
            ),
        )

        create_audit_log(
            db,
            user=actor,
            action=ACTION_CREATE,
            entity_type=ENTITY_TYPE_BATCH,
            entity_id=saved.id,
            details={
                "medicine_id": saved.medicine_id,
                "batch_number": saved.batch_number,
                "quantity_received": payload.quantity_received,
                "status": saved.status,
            },
            ip_address=ip_address,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch number already exists for this medicine",
        ) from exc
    except Exception:
        db.rollback()
        raise

    db.refresh(saved)
    return serialize_batch(saved)


def list_movement_records(
    db: Session,
    *,
    limit: int,
    offset: int,
    medicine_id: int | None = None,
    batch_id: int | None = None,
) -> dict:
    movements, total = repository.fetch_inventory_movements(
        db,
        limit=limit,
        offset=offset,
        medicine_id=medicine_id,
        batch_id=batch_id,
    )
    payload = InventoryMovementListResponse(
        items=[InventoryMovementResponse.model_validate(item) for item in movements],
        total=total,
        limit=limit,
        offset=offset,
    )
    return payload.model_dump(mode="json")
