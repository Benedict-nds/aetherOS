from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class RefundItem(Base):
    __tablename__ = "refund_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    refund_id: Mapped[int] = mapped_column(
        ForeignKey("refunds.id", ondelete="CASCADE"),
        nullable=False,
    )
    sale_line_id: Mapped[int] = mapped_column(
        ForeignKey("sale_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    return_to_stock: Mapped[bool] = mapped_column(Boolean, nullable=False)

    refund = relationship("Refund", back_populates="items")
    sale_line = relationship("SaleLine", back_populates="refund_items")
