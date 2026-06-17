"""add_pais_destino_exportacion_a_fel

Revision ID: 0ac22d9e4e4d
Revises: a04d7a906683
Create Date: 2026-06-16 10:29:34.993903

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0ac22d9e4e4d'
down_revision: Union[str, None] = 'a04d7a906683'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Skip para el tenant 'system' (esquema vacío para superadmin)
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # Agregar el campo pais_destino_exportacion a facturas_electronicas
    op.add_column(
        'facturas_electronicas', 
        sa.Column('pais_destino_exportacion', sa.String(100), nullable=True)
    )
    
    # Opcional: Índice para acelerar consultas de exportaciones por país
    op.create_index(
        'idx_facturas_pais_destino', 
        'facturas_electronicas', 
        ['pais_destino_exportacion']
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    op.drop_index('idx_facturas_pais_destino', table_name='facturas_electronicas')
    op.drop_column('facturas_electronicas', 'pais_destino_exportacion')