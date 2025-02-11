"""add_relationship_between_block_entrypoint

Revision ID: 18f3f9de3ea4
Revises: 0320e7c7803a
Create Date: 2025-01-22 19:12:26.236527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18f3f9de3ea4'
down_revision: Union[str, None] = '0320e7c7803a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('blocks', sa.Column('selected_entrypoint_uuid', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_selected_entrypoint_uuid', 'blocks', 'entrypoints', ['selected_entrypoint_uuid'], ['uuid'], ondelete='SET NULL')
    op.alter_column('entrypoints', 'block_uuid',
               existing_type=sa.UUID(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('entrypoints', 'block_uuid',
               existing_type=sa.UUID(),
               nullable=True)
    op.drop_constraint('fk_selected_entrypoint_uuid', 'blocks', type_='foreignkey')
    op.drop_column('blocks', 'selected_entrypoint_uuid')
    # ### end Alembic commands ###
