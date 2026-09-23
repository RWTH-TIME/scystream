"""add superset synced run id

Revision ID: c7d2e9f1a3b4
Revises: a1b2c3d4e5f6
Create Date: 2026-09-23 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d2e9f1a3b4"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("superset_synced_run_id", sa.String(length=250),
                  nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "superset_synced_run_id")
