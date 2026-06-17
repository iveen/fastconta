"""add_campos_declaraciones_sat_a_facturas

Revision ID: 9ffed37a95d6
Revises: 1d25e0969673
Create Date: 2026-06-15 08:58:54.917203

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9ffed37a95d6'
down_revision: Union[str, None] = '1d25e0969673'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return    
    # Agregar los nuevos campos a facturas_electronicas
    op.add_column('facturas_electronicas', sa.Column('retencion_iva', sa.Numeric(12, 2), server_default='0'))
    op.add_column('facturas_electronicas', sa.Column('retencion_isr', sa.Numeric(12, 2), server_default='0'))
    op.add_column('facturas_electronicas', sa.Column('clasificacion_gasto_sat', sa.String(50), server_default='NORMAL'))
    op.add_column('facturas_electronicas', sa.Column('es_importacion', sa.Boolean, server_default='false'))



def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_column('facturas_electronicas', 'es_importacion')
    op.drop_column('facturas_electronicas', 'clasificacion_gasto_sat')
    op.drop_column('facturas_electronicas', 'retencion_isr')
    op.drop_column('facturas_electronicas', 'retencion_iva')
