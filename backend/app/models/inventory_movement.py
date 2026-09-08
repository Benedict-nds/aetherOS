from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    medicine = relationship("Medicine", back_populates="inventory_movements")
    batch = relationship("Batch", back_populates="inventory_movements")
    user = relationship("User")
