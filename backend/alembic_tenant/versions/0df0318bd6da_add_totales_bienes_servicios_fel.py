"""add_totales_bienes_servicios_fel

Revision ID: 0df0318bd6da
Revises: 429eb54a1335
Create Date: 2026-06-16 16:08:55.487715

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0df0318bd6da'
down_revision: Union[str, None] = '429eb54a1335'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # Agregar columnas para totales separados
    op.add_column('facturas_electronicas', sa.Column('total_gravado_bienes', sa.Numeric(12, 2), default=0))
    op.add_column('facturas_electronicas', sa.Column('total_iva_bienes', sa.Numeric(12, 2), default=0))
    op.add_column('facturas_electronicas', sa.Column('total_gravado_servicios', sa.Numeric(12, 2), default=0))
    op.add_column('facturas_electronicas', sa.Column('total_iva_servicios', sa.Numeric(12, 2), default=0))
    
    op.add_column('facturas_electronicas', sa.Column('total_gravado_bienes_gtq', sa.Numeric(15, 2), default=0))
    op.add_column('facturas_electronicas', sa.Column('total_iva_bienes_gtq', sa.Numeric(15, 2), default=0))
    op.add_column('facturas_electronicas', sa.Column('total_gravado_servicios_gtq', sa.Numeric(15, 2), default=0))
    op.add_column('facturas_electronicas', sa.Column('total_iva_servicios_gtq', sa.Numeric(15, 2), default=0))
    

def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    op.drop_column('facturas_electronicas', 'total_iva_servicios_gtq')
    op.drop_column('facturas_electronicas', 'total_gravado_servicios_gtq')
    op.drop_column('facturas_electronicas', 'total_iva_bienes_gtq')
    op.drop_column('facturas_electronicas', 'total_gravado_bienes_gtq')
    op.drop_column('facturas_electronicas', 'total_iva_servicios')
    op.drop_column('facturas_electronicas', 'total_gravado_servicios')
    op.drop_column('facturas_electronicas', 'total_iva_bienes')
    op.drop_column('facturas_electronicas', 'total_gravado_bienes')
