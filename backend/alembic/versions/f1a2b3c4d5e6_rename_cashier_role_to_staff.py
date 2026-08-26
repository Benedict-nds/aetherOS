"""rename cashier role to staff

Revision ID: f1a2b3c4d5e6
Revises: d25b8450e015
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "d25b8450e015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE roles
            SET name = 'staff', description = 'Pharmacy staff'
            WHERE name = 'cashier'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE roles
            SET name = 'cashier', description = 'Pharmacy cashier'
            WHERE name = 'staff'
            """
        )
    )
