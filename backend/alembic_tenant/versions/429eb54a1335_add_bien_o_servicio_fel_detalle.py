"""add_bien_o_servicio_fel_detalle

Revision ID: 429eb54a1335
Revises: 0ac22d9e4e4d
Create Date: 2026-06-16 15:37:24.431177

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '429eb54a1335'
down_revision: Union[str, None] = '0ac22d9e4e4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    op.add_column(
        'factura_detalles', 
        sa.Column('bien_o_servicio', sa.String(1), nullable=False, server_default='B')
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    op.drop_column('factura_detalles', 'bien_o_servicio')
