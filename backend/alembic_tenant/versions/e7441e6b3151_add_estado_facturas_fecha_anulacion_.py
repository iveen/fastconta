"""add: estado facturas, fecha anulacion, impuestos especiales

Revision ID: e7441e6b3151
Revises: ff964c9ca097
Create Date: 2026-05-26 12:03:57.153756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = 'e7441e6b3151'
down_revision: Union[str, None] = 'ff964c9ca097'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # 1. Añadir columna fecha_anulacion a facturas_electronicas
    op.add_column(
        'facturas_electronicas',
        sa.Column('fecha_anulacion', sa.DateTime(timezone=True), nullable=True)
    )

    # 2. Crear tabla de impuestos con FK hacia public.catalogo_impuestos_especiales
    op.create_table(
        'facturas_impuestos_especiales',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('factura_id', sa.UUID(), sa.ForeignKey('facturas_electronicas.id'), nullable=False, index=True),
        
        # ✅ FK Cross-Schema (tenant -> public)
        sa.Column('catalogo_id', sa.UUID(), sa.ForeignKey('public.catalogo_impuestos_especiales.id'), nullable=False, index=True),
        
        sa.Column('monto', sa.Numeric(12, 2), server_default='0', nullable=False)
    )

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # 1. Eliminar tabla hija
    op.drop_table('facturas_impuestos_especiales')
    # 2. Eliminar columna
    op.drop_column('facturas_electronicas', 'fecha_anulacion')
