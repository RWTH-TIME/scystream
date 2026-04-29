"""change pgtype to dbtype

Revision ID: 02a29087557a
Revises: f64b79e16ea0
Create Date: 2026-04-13 17:32:23.885495

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "02a29087557a"
down_revision: Union[str, None] = "f64b79e16ea0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE datatype RENAME TO datatype_old")

    op.execute("CREATE TYPE datatype AS ENUM ('DBTABLE', 'FILE', 'CUSTOM')")

    op.execute(
        """
        ALTER TABLE inputoutputs
        ALTER COLUMN data_type
        TYPE datatype
        USING (
            CASE
                WHEN data_type::text = 'PGTABLE' THEN 'DBTABLE'
                WHEN data_type::text = 'FILE' THEN 'FILE'
                WHEN data_type::text = 'CUSTOM' THEN 'CUSTOM'
                ELSE data_type::text
            END
        )::datatype
        """
    )

    # 4. Drop old enum
    op.execute("DROP TYPE datatype_old")


def downgrade() -> None:
    # 1. Rename current enum
    op.execute("ALTER TYPE datatype RENAME TO datatype_new")

    # 2. Recreate old enum (lowercase values!)
    op.execute("CREATE TYPE datatype AS ENUM ('PGTABLE', 'FILE', 'CUSTOM')")

    # 3. Convert column back (MATCH CASE EXACTLY)
    op.execute(
        """
        ALTER TABLE inputoutputs
        ALTER COLUMN data_type
        TYPE datatype
        USING (
            CASE
                WHEN data_type::text = 'DBTABLE' THEN 'PGTABLE'
                WHEN data_type::text = 'FILE' THEN 'FILE'
                WHEN data_type::text = 'CUSTOM' THEN 'CUSTOM'
                ELSE data_type::text
            END
        )::datatype
        """
    )

    # 4. Drop new enum
    op.execute("DROP TYPE datatype_new")
