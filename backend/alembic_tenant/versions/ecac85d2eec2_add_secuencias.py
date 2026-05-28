"""add_secuencias

Revision ID: ecac85d2eec2
Revises: a989a89a0415
Create Date: 2026-05-19 11:56:52.804872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'ecac85d2eec2'
down_revision: Union[str, None] = 'a989a89a0415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.create_table(
        'secuencias',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entidad', sa.String(50), nullable=False),
        sa.Column('empresa_id', UUID(as_uuid=True), nullable=False),
        sa.Column('contador', sa.Integer(), server_default='1'),
        sa.UniqueConstraint('entidad', 'empresa_id', name='uq_secuencias_entidad_empresa'),
        schema=tenant_schema
    )
    op.create_foreign_key('fk_secuencias_empresa', 'secuencias', 'empresas',
                          ['empresa_id'], ['id'],
                          source_schema=tenant_schema, referent_schema=tenant_schema)

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_constraint('fk_secuencias_empresa', 'secuencias', schema=tenant_schema)
    op.drop_table('secuencias', schema=tenant_schema)