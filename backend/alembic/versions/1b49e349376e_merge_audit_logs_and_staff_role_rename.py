"""merge audit logs and staff role rename

Revision ID: 1b49e349376e
Revises: cd544c6f7d21, f1a2b3c4d5e6
Create Date: 2026-08-31 03:35:30.179124

"""

from typing import Sequence, Union

revision: str = "1b49e349376e"
down_revision: Union[str, Sequence[str], None] = ("cd544c6f7d21", "f1a2b3c4d5e6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
