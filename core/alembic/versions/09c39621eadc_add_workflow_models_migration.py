"""add workflow models migration

Revision ID: 09c39621eadc
Revises: 11cb4f286ec5
Create Date: 2024-10-31 10:13:54.589121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09c39621eadc'
down_revision: Union[str, None] = '11cb4f286ec5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('projects',
    sa.Column('uuid', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('uuid')
    )
    op.create_table('blocks',
    sa.Column('uuid', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('project_uuid', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['project_uuid'], ['projects.uuid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('uuid')
    )
    op.create_table('user_project',
    sa.Column('user_uuid', sa.UUID(), nullable=False),
    sa.Column('project_uuid', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['project_uuid'], ['projects.uuid'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_uuid'], ['users.uuid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_uuid', 'project_uuid')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_project')
    op.drop_table('blocks')
    op.drop_table('projects')
    # ### end Alembic commands ###