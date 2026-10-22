from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.sale import Sale
from app.models.sale_line import SaleLine
from app.models.user import User
from app.modules.inventory.repository import insert_inventory_movement
from app.modules.inventory.service import apply_quantity_change
from app.modules.audit.service import create_audit_log, ENTITY_TYPE_SALE
from app.modules.sales import repository
from app.modules.sales.schemas import SaleCreate, SaleLineResponse, SaleResponse

MOVEMENT_TYPE_STOCK_OUT = "stock_out"
REFERENCE_TYPE_SALE = "sale"


@dataclass(frozen=True)
class _Allocation:
    batch: Batch
    medicine_id: int
    quantity: int
    unit_price: Decimal


def _locked_batches_by_medicine(
    db: Session,
    *,
    medicine_ids: list[int],
    as_of,
) -> dict[int, list[Batch]]:
    by_medicine: dict[int, list[Batch]] = {}
    for medicine_id in medicine_ids:
        if medicine_id in by_medicine:
            continue
        if not repository.medicine_exists(db, medicine_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found",
            )
        by_medicine[medicine_id] = repository.fetch_fefo_batches_for_update(
            db,
            medicine_id=medicine_id,
            as_of=as_of,
        )
    return by_medicine


def _plan_sale_allocations(
    batches_by_medicine: dict[int, list[Batch]],
    lines: list,
    *,
    as_of,
) -> list[_Allocation]:
    remaining_by_batch: dict[int, int] = {}
    for batches in batches_by_medicine.values():
        for batch in batches:
            remaining_by_batch[batch.id] = batch.quantity_on_hand

    allocations: list[_Allocation] = []

    for line in lines:
        remaining = line.quantity
        for batch in batches_by_medicine[line.medicine_id]:
            if remaining <= 0:
                break
            if batch.status == "void":
                continue
            if batch.expiry_date is not None and batch.expiry_date < as_of:
                continue
            available = remaining_by_batch.get(batch.id, 0)
            if available <= 0:
                continue
            take = min(available, remaining)
            allocations.append(
                _Allocation(
                    batch=batch,
                    medicine_id=line.medicine_id,
                    quantity=take,
                    unit_price=batch.selling_price,
                )
            )
            remaining_by_batch[batch.id] = available - take
            remaining -= take

        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Insufficient stock to complete sale",
            )

    return allocations


def create_sale_record(db: Session, actor: User, payload: SaleCreate) -> dict:
    as_of = datetime.now(timezone.utc).date()
    medicine_ids = list(dict.fromkeys(line.medicine_id for line in payload.lines))

    try:
        batches_by_medicine = _locked_batches_by_medicine(
            db,
            medicine_ids=medicine_ids,
            as_of=as_of,
        )
        allocations = _plan_sale_allocations(
            batches_by_medicine,
            payload.lines,
            as_of=as_of,
        )
        total = sum(a.unit_price * a.quantity for a in allocations)
        amount_paid = payload.amount_paid if payload.payment_method == "cash" and payload.amount_paid is not None else total
        if amount_paid < total:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Amount paid is less than the sale total",
            )
        change_due = amount_paid - total

        sale = Sale(
            payment_method=payload.payment_method,
            total=total,
            amount_paid=amount_paid,
            change_due=change_due,
            user_id=actor.id,
        )
        repository.insert_sale(db, sale)

        for alloc in allocations:
            apply_quantity_change(alloc.batch, -alloc.quantity)
            insert_inventory_movement(
                db,
                InventoryMovement(
                    medicine_id=alloc.medicine_id,
                    batch_id=alloc.batch.id,
                    movement_type=MOVEMENT_TYPE_STOCK_OUT,
                    quantity_change=-alloc.quantity,
                    reference_type=REFERENCE_TYPE_SALE,
                    reference_id=sale.id,
                    user_id=actor.id,
                ),
            )
            repository.insert_sale_line(
                db,
                SaleLine(
                    sale_id=sale.id,
                    batch_id=alloc.batch.id,
                    medicine_id=alloc.medicine_id,
                    quantity=alloc.quantity,
                    unit_price=alloc.unit_price,
                    cost_price_snapshot=alloc.batch.cost_price,
                ),
            )

        create_audit_log(
            db,
            action="sale.created",
            entity_type=ENTITY_TYPE_SALE,
            user=actor,
            entity_id=sale.id,
            details={
                "total": str(total),
                "payment_method": payload.payment_method,
                "line_count": len(allocations),
            },
        )
        db.commit()
        sale = repository.get_sale(db, sale.id)
        assert sale is not None
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return serialize_sale(sale)


def serialize_sale(sale: Sale) -> dict:
    return SaleResponse(
        id=sale.id,
        payment_method=sale.payment_method,
        total=sale.total,
        amount_paid=sale.amount_paid,
        change_due=sale.change_due,
        user_id=sale.user_id,
        cashier={"id": sale.user.id, "full_name": sale.user.full_name},
        lines=[
            SaleLineResponse(
                id=line.id,
                batch_id=line.batch_id,
                medicine_id=line.medicine_id,
                medicine_name=line.medicine.name,
                batch_number=line.batch.batch_number,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.unit_price * line.quantity,
            )
            for line in sale.lines
        ],
        created_at=sale.created_at.isoformat(),
    ).model_dump()


def get_sale_record(db: Session, sale_id: int) -> dict:
    sale = repository.get_sale(db, sale_id)
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    return serialize_sale(sale)


def sum_today_sales_amount(db: Session) -> float:
    today = datetime.now(timezone.utc).date()
    total = repository.sum_sales_total_for_utc_day(db, day=today)
    return float(total)
