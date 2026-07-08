"""delete_max_companies_limit_on_tenant

Revision ID: 06c750bb6c0c
Revises: 3769f118301e
Create Date: 2026-07-07 11:57:55.022187

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '06c750bb6c0c'
down_revision: Union[str, None] = '3769f118301e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Eliminar columna max_empresas
    op.drop_column('tenants', 'max_empresas', schema='public')
    
    # 2. Agregar campos de trial
    op.add_column(
        'tenants',
        sa.Column(
            'trial_until',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Fecha de expiración del trial. NULL = sin trial activo'
        ),
        schema='public'
    )
    
    op.add_column(
        'tenants',
        sa.Column(
            'trial_max_usuarios',
            sa.Integer(),
            nullable=True,
            comment='Límite de usuarios durante el trial. NULL = usa max_usuarios del plan'
        ),
        schema='public'
    )
    
    # 3. Crear índice para búsquedas por trial (útil para jobs de expiración)
    op.create_index(
        'ix_public_tenants_trial_until',
        'tenants',
        ['trial_until'],
        unique=False,
        schema='public'
    )
    
    # 4. Actualizar datos existentes: mover max_empresas a un valor razonable
    # Como ya no se usa, no necesitamos migrar datos, solo asegurar que max_usuarios
    # tenga un valor por defecto sensato para tenants existentes
    op.execute("""
        UPDATE public.tenants 
        SET max_usuarios = 3 
        WHERE max_usuarios IS NULL OR max_usuarios = 0
    """)


def downgrade() -> None:
    # 1. Eliminar índice de trial
    op.drop_index('ix_public_tenants_trial_until', table_name='tenants', schema='public')
    
    # 2. Eliminar campos de trial
    op.drop_column('tenants', 'trial_max_usuarios', schema='public')
    op.drop_column('tenants', 'trial_until', schema='public')
    
    # 3. Restaurar max_empresas con valor por defecto
    op.add_column(
        'tenants',
        sa.Column('max_empresas', sa.Integer(), nullable=False, server_default='5'),
        schema='public'
    )