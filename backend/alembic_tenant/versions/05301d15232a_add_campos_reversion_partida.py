"""add_campos_reversion_partida

Revision ID: 05301d15232a
Revises: 3116febc6457
Create Date: 2026-06-09 16:27:07.389892

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '05301d15232a'
down_revision: Union[str, None] = '3116febc6457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # ✅ Agregar campo fue_revertida con default FALSE
    # Esto llenará automáticamente todas las filas existentes con FALSE
    op.add_column(
        'partidas',
        sa.Column(
            'fue_revertida',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')
        )
    )
    
    # ✅ Agregar campo partida_reversion_id (nullable porque solo se llena cuando se revierte)
    op.add_column(
        'partidas',
        sa.Column(
            'partida_reversion_id',
            sa.UUID(),
            nullable=True
        )
    )
    
    # ✅ Agregar foreign key constraint
    op.create_foreign_key(
        'fk_partidas_partida_reversion_id',
        'partidas',
        'partidas',
        ['partida_reversion_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # ✅ Eliminar foreign key primero
    op.drop_constraint('fk_partidas_partida_reversion_id', 'partidas', type_='foreignkey')
    
    # ✅ Eliminar columnas
    op.drop_column('partidas', 'partida_reversion_id')
    op.drop_column('partidas', 'fue_revertida')
