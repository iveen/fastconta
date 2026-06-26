"""add_is_active_to_regimenes

Revision ID: 3f6a91a9cedf
Revises: cdf4931118a9
Create Date: 2026-06-18 20:39:03.842019

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3f6a91a9cedf'
down_revision: Union[str, None] = 'cdf4931118a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna is_active a regimenes_fiscales
    op.add_column(
        'regimenes_fiscales',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        schema='public'
    )
    print("✅ Columna is_active agregada a regimenes_fiscales")


def downgrade() -> None:
    # Eliminar columna is_active
    op.drop_column('regimenes_fiscales', 'is_active', schema='public')
    print("✅ Columna is_active eliminada de regimenes_fiscales")
