"""add_campos_partida

Revision ID: b784c4ae6e9d
Revises: 90dab873f830
Create Date: 2026-05-18 11:16:57.239837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'b784c4ae6e9d'
down_revision: Union[str, None] = '90dab873f830'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.execute(f"CREATE SEQUENCE IF NOT EXISTS {tenant_schema}.partidas_numero_seq")
    op.add_column('partidas',
                  sa.Column('numero', sa.Integer(), nullable=False,
                            server_default=sa.text(f"nextval('{tenant_schema}.partidas_numero_seq')")),
                  schema=tenant_schema)
    op.add_column('partidas',
                  sa.Column('numero_poliza', sa.String(50), nullable=True, unique=True),
                  schema=tenant_schema)
    op.add_column('partidas',
                  sa.Column('empresa_id', UUID(as_uuid=True), nullable=False),
                  schema=tenant_schema)
    op.create_unique_constraint('uq_partidas_numero', 'partidas', ['numero'], schema=tenant_schema)
    op.create_foreign_key('fk_partidas_empresa', 'partidas', 'empresas',
                          ['empresa_id'], ['id'],
                          source_schema=tenant_schema, referent_schema=tenant_schema)

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_constraint('fk_partidas_empresa', 'partidas', schema=tenant_schema)
    op.drop_constraint('uq_partidas_numero', 'partidas', schema=tenant_schema)
    op.drop_column('partidas', 'empresa_id', schema=tenant_schema)
    op.drop_column('partidas', 'numero_poliza', schema=tenant_schema)
    op.drop_column('partidas', 'numero', schema=tenant_schema)
    op.execute(f"DROP SEQUENCE IF EXISTS {tenant_schema}.partidas_numero_seq")