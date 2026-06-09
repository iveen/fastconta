"""add_is_active_to_partidas_and_detalles

Revision ID: 3116febc6457
Revises: 5a0b7b26423e
Create Date: 2026-06-09 11:03:56.341680

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3116febc6457'
down_revision: Union[str, None] = '5a0b7b26423e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # 1. Agregar columna is_active a la tabla 'partidas'
    # Usamos server_default='true' para que PostgreSQL lo maneje a nivel de BD
    op.add_column(
        'partidas',
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False)
    )
    
    # 2. Agregar columna is_active a la tabla 'detalle_partidas'
    op.add_column(
        'detalle_partidas',
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False)
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # 1. Eliminar columna de 'detalle_partidas' primero (por si hay dependencias, aunque aquí no las hay)
    op.drop_column('detalle_partidas', 'is_active')
    
    # 2. Eliminar columna de 'partidas'
    op.drop_column('partidas', 'is_active')
