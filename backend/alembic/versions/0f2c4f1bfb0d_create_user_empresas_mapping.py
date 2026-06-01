"""create_user_empresas_mapping

Revision ID: 0f2c4f1bfb0d
Revises: 11dbf33816ed
Create Date: 2026-05-31 20:30:08.580115

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '0f2c4f1bfb0d'
down_revision: Union[str, None] = 'e07f2492716c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'user_empresas',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('public.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('public.tenants.id', ondelete='CASCADE'), nullable=False),
        # 👇 Referencia lógica a empresas. NO lleva ForeignKey porque empresas vive en schema dinámico
        sa.Column('empresa_id', UUID(as_uuid=True), nullable=False),
        sa.Column('activo', sa.Boolean(), server_default='true', default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        # Restricción de unicidad compuesta
        sa.UniqueConstraint('user_id', 'tenant_id', 'empresa_id', name='uq_user_empresa_tenant'),
        schema='public'
    )
    
    # Índices optimizados para consultas frecuentes
    op.create_index('ix_user_empresas_tenant_user', 'user_empresas', ['tenant_id', 'user_id'], schema='public')
    op.create_index('ix_user_empresas_empresa', 'user_empresas', ['empresa_id'], schema='public')

def downgrade():
    op.drop_index('ix_user_empresas_empresa', table_name='user_empresas', schema='public')
    op.drop_index('ix_user_empresas_tenant_user', table_name='user_empresas', schema='public')
    op.drop_table('user_empresas', schema='public')