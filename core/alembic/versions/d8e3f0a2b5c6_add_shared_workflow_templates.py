"""add shared workflow templates

Revision ID: d8e3f0a2b5c6
Revises: c7d2e9f1a3b4
Create Date: 2026-09-23 11:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d8e3f0a2b5c6"
down_revision: Union[str, None] = "c7d2e9f1a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shared_workflow_templates",
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=50)),
                  nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("superset_template_s3_key", sa.String(length=512),
                  nullable=True),
        sa.Column("source_project_uuid", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_by_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("uuid"),
    )


def downgrade() -> None:
    op.drop_table("shared_workflow_templates")
