from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.supplier import Supplier


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    return db.get(Supplier, supplier_id)


def get_batch_by_medicine_and_number(
    db: Session, medicine_id: int, batch_number: str
) -> Batch | None:
    return db.scalar(
        select(Batch).where(
            Batch.medicine_id == medicine_id,
            Batch.batch_number == batch_number,
        )
    )
