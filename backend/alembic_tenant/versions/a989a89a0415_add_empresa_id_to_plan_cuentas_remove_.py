"""add_empresa_id_to_plan_cuentas_remove_from_partidas

Revision ID: a989a89a0415
Revises: b784c4ae6e9d
Create Date: 2026-05-18 16:39:48.631171

"""
from typing import Sequence, Union
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a989a89a0415'
down_revision: Union[str, None] = 'b784c4ae6e9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.add_column('plan_cuentas', sa.Column('empresa_id', UUID(as_uuid=True), nullable=False), schema=tenant_schema)
    op.create_foreign_key('fk_plan_cuentas_empresa', 'plan_cuentas', 'empresas',
                          ['empresa_id'], ['id'],
                          source_schema=tenant_schema, referent_schema=tenant_schema)
    op.drop_constraint('fk_partidas_empresa', 'partidas', schema=tenant_schema)
    op.drop_column('partidas', 'empresa_id', schema=tenant_schema)

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.add_column('partidas', sa.Column('empresa_id', UUID(as_uuid=True), nullable=True), schema=tenant_schema)
    op.create_foreign_key('fk_partidas_empresa', 'partidas', 'empresas',
                          ['empresa_id'], ['id'],
                          source_schema=tenant_schema, referent_schema=tenant_schema)
    op.drop_constraint('fk_plan_cuentas_empresa', 'plan_cuentas', schema=tenant_schema)
    op.drop_column('plan_cuentas', 'empresa_id', schema=tenant_schema)