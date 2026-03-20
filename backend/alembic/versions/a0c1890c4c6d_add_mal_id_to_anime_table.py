"""add mal_id to anime table

Revision ID: a0c1890c4c6d
Revises: 358245db7a4b
Create Date: 2026-03-01 00:41:36.251139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a0c1890c4c6d'
down_revision: Union[str, Sequence[str], None] = '358245db7a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('anime', sa.Column('mal_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_anime_mal_id'), 'anime', ['mal_id'], unique=False)
    # ### end Alembic commands ###

def downgrade() -> None:
    op.drop_index(op.f('ix_anime_mal_id'), table_name='anime')
    op.drop_column('anime', 'mal_id')
    # ### end Alembic commands ###
