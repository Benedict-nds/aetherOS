from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.inventory.schemas import BatchCreate
from app.modules.inventory.service import create_batch_record
from app.modules.purchases import repository
from app.modules.purchases.schemas import ReceiptCreate


def create_receipt_record(db: Session, actor: User, payload: ReceiptCreate, *, ip_address: str | None = None) -> list[dict]:
    supplier = repository.get_supplier(db, payload.supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not supplier.is_active:
        raise HTTPException(status_code=409, detail="Supplier is inactive")

    created = []
    try:
        for line in payload.lines:
            batch_number = line.batch_number.strip()
            if repository.get_batch_by_medicine_and_number(db, line.medicine_id, batch_number):
                raise HTTPException(status_code=409, detail="Batch number already exists for this medicine")
            created.append(create_batch_record(
                db,
                actor,
                BatchCreate(
                    medicine_id=line.medicine_id,
                    batch_number=batch_number,
                    expiry_date=line.expiry_date,
                    cost_price=line.cost_price,
                    selling_price=line.selling_price,
                    quantity_received=line.quantity_received,
                ),
                ip_address=ip_address,
                supplier_id=supplier.id,
                commit=False,
            ))
        db.commit()
        return created
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Batch number already exists for this medicine") from exc
    except Exception:
        db.rollback()
        raise
