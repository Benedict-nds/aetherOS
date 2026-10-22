"""add sale payment and cost snapshot

Revision ID: e8f0a1b2c3d4
Revises: cd544c6f7d21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e8f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = (
    "b8d4f9a21c56",
    "1b49e349376e",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sales", sa.Column("amount_paid", sa.Numeric(12, 2), nullable=True))
    op.add_column("sales", sa.Column("change_due", sa.Numeric(12, 2), nullable=True))
    op.add_column(
        "sale_lines",
        sa.Column("cost_price_snapshot", sa.Numeric(12, 2), nullable=True),
    )
    op.execute(sa.text("UPDATE sales SET amount_paid = total, change_due = 0"))
    op.execute(
        sa.text(
            "UPDATE sale_lines SET cost_price_snapshot = "
            "(SELECT cost_price FROM batches WHERE batches.id = sale_lines.batch_id)"
        )
    )
    with op.batch_alter_table("sales") as batch_op:
        batch_op.alter_column("amount_paid", existing_type=sa.Numeric(12, 2), nullable=False)
        batch_op.alter_column("change_due", existing_type=sa.Numeric(12, 2), nullable=False)
    with op.batch_alter_table("sale_lines") as batch_op:
        batch_op.alter_column(
            "cost_price_snapshot",
            existing_type=sa.Numeric(12, 2),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("sale_lines") as batch_op:
        batch_op.drop_column("cost_price_snapshot")
    with op.batch_alter_table("sales") as batch_op:
        batch_op.drop_column("change_due")
        batch_op.drop_column("amount_paid")