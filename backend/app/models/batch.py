from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    medicine = relationship("Medicine", back_populates="batches")
    inventory_movements = relationship("InventoryMovement", back_populates="batch")
