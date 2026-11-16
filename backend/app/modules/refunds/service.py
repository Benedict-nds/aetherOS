from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inventory_movement import InventoryMovement
from app.models.refund import Refund
from app.models.refund_item import RefundItem
from app.models.sale_line import SaleLine
from app.models.user import User
from app.modules.audit.service import ENTITY_TYPE_REFUND, create_audit_log
from app.modules.inventory.repository import insert_inventory_movement
from app.modules.inventory.service import apply_quantity_change
from app.modules.refunds import repository
from app.modules.refunds.schemas import RefundCreate, RefundLineResponse, RefundResponse

MOVEMENT_TYPE_REFUND = "refund"
REFERENCE_TYPE_REFUND = "refund"
REFUND_STATUS_COMPLETED = "completed"


def _generate_refund_number() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"RFD-{timestamp}"


def _serialize_refund(refund: Refund) -> dict:
    return RefundResponse(
        id=refund.id,
        refund_number=refund.refund_number,
        sale_id=refund.sale_id,
        reason=refund.reason,
        refund_method=refund.refund_method,
        total_amount=refund.total_amount,
        created_at=refund.created_at.isoformat(),
        cashier={"id": refund.user.id, "full_name": refund.user.full_name},
        lines=[
            RefundLineResponse(
                sale_line_id=item.sale_line_id,
                medicine_id=item.sale_line.medicine_id,
                medicine_name=item.sale_line.medicine.name,
                batch_id=item.sale_line.batch_id,
                quantity=item.quantity,
                amount=item.amount,
                return_to_stock=item.return_to_stock,
            )
            for item in refund.items
        ],
    ).model_dump()


def create_refund_record(db: Session, actor: User, payload: RefundCreate) -> dict:
    sale = repository.get_sale_for_refund(db, payload.sale_id)
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

    requested_line_ids = [line.sale_line_id for line in payload.lines]
    if len(set(requested_line_ids)) != len(requested_line_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Duplicate sale_line_id values are not allowed",
        )

    locked_sale_lines = repository.get_sale_lines_for_update(
        db,
        sale_id=sale.id,
        line_ids=requested_line_ids,
    )
    sale_line_by_id = {line.id: line for line in locked_sale_lines}

    if len(sale_line_by_id) != len(requested_line_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more sale lines do not belong to the sale",
        )

    refunded_by_line = repository.get_refunded_quantities_by_sale_line(
        db,
        sale_line_ids=requested_line_ids,
    )

    try:
        total_amount = Decimal("0.00")
        validated_lines: list[tuple[SaleLine, int, Decimal, bool]] = []
        for line in payload.lines:
            sale_line = sale_line_by_id[line.sale_line_id]
            already_refunded = refunded_by_line.get(sale_line.id, 0)
            available = sale_line.quantity - already_refunded
            if line.quantity > available:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Refund quantity exceeds remaining sold quantity",
                )

            amount = sale_line.unit_price * line.quantity
            total_amount += amount
            validated_lines.append(
                (sale_line, line.quantity, amount, line.return_to_stock)
            )

        refund = repository.insert_refund(
            db,
            Refund(
                sale_id=sale.id,
                refund_number=_generate_refund_number(),
                user_id=actor.id,
                reason=payload.reason,
                total_amount=total_amount,
                refund_method=payload.refund_method,
                status=REFUND_STATUS_COMPLETED,
            ),
        )

        for sale_line, quantity, amount, return_to_stock in validated_lines:
            repository.insert_refund_item(
                db,
                RefundItem(
                    refund_id=refund.id,
                    sale_line_id=sale_line.id,
                    quantity=quantity,
                    amount=amount,
                    return_to_stock=return_to_stock,
                ),
            )

            if return_to_stock:
                apply_quantity_change(sale_line.batch, quantity)
                insert_inventory_movement(
                    db,
                    InventoryMovement(
                        medicine_id=sale_line.medicine_id,
                        batch_id=sale_line.batch_id,
                        movement_type=MOVEMENT_TYPE_REFUND,
                        quantity_change=quantity,
                        reference_type=REFERENCE_TYPE_REFUND,
                        reference_id=refund.id,
                        reason=payload.reason,
                        user_id=actor.id,
                    ),
                )

        create_audit_log(
            db,
            user=actor,
            action="refund.created",
            entity_type=ENTITY_TYPE_REFUND,
            entity_id=refund.id,
            details={
                "sale_id": sale.id,
                "total_amount": str(total_amount),
                "line_count": len(validated_lines),
                "refund_method": payload.refund_method,
            },
        )

        db.commit()
        persisted = repository.get_refund(db, refund.id)
        assert persisted is not None
        return _serialize_refund(persisted)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
