"""add_descripcion_tipo_persona

Revision ID: 6ae007510c23
Revises: 62b673b5e008
Create Date: 2026-07-02 14:34:32.272440

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6ae007510c23'
down_revision: Union[str, None] = '62b673b5e008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tipos_persona',
        sa.Column('descripcion', sa.String(200), nullable=True),
        schema='public'
    )


def downgrade() -> None:
    op.drop_column('tipos_persona', 'descripcion', schema='public')
