"""add superset dashboard fields

Revision ID: a1b2c3d4e5f6
Revises: 02a29087557a
Create Date: 2026-05-27 12:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "02a29087557a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("owner_email", sa.String(255), nullable=True))
    op.add_column(
        "projects", sa.Column("superset_export_s3_key", sa.String(512), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("superset_dashboard_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("superset_dashboard_url", sa.String(1024), nullable=True)
    )
    op.add_column(
        "projects",
        sa.Column(
            "superset_import_status",
            sa.String(32),
            nullable=False,
            server_default="none",
        ),
    )
    op.add_column(
        "projects", sa.Column("superset_import_error", sa.String(2048), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("projects", "superset_import_error")
    op.drop_column("projects", "superset_import_status")
    op.drop_column("projects", "superset_dashboard_url")
    op.drop_column("projects", "superset_dashboard_id")
    op.drop_column("projects", "superset_export_s3_key")
    op.drop_column("projects", "owner_email")
