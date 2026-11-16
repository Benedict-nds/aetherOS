"""merge sales and suppliers heads

Revision ID: aa11bb22cc33
Revises: c71d3f8a2b91, e8f0a1b2c3d4
Create Date: 2026-11-04 20:48:00.000000
"""
from typing import Sequence, Union


revision: str = "aa11bb22cc33"
down_revision: Union[str, Sequence[str], None] = (
    "c71d3f8a2b91",
    "e8f0a1b2c3d4",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
