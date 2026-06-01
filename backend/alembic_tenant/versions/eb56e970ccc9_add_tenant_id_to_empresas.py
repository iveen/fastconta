"""add_tenant_id_to_empresas

Revision ID: eb56e970ccc9
Revises: 11dbf33816ed
Create Date: 2026-05-31 20:40:33.979275

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'eb56e970ccc9'
down_revision: Union[str, None] = '11dbf33816ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # 1. Añadir columna como NULLABLE inicialmente para evitar bloqueo en producción
    op.add_column(
        'empresas',
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('public.tenants.id'), nullable=True),
    )
    
    # 2. Índice para búsquedas por tenant
    op.create_index('ix_empresas_tenant_id', 'empresas', ['tenant_id'])
    
    # 📝 PASO OBLIGATORIO: Backfill antes de hacer NOT NULL
    # Ejecuta esto manualmente o en un script post-migración:
    # UPDATE empresas SET tenant_id = '<UUID_TENANT_ACTUAL>' WHERE tenant_id IS NULL;
    
    # 3. Una vez validado el backfill, descomenta para forzar integridad:
    op.alter_column('empresas', 'tenant_id', nullable=False)

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_index('ix_empresas_tenant_id', table_name='empresas')
    op.drop_column('empresas', 'tenant_id')
