"""add_auditable_full_reg_attempts

Revision ID: 7696be83c1bf
Revises: d11d9574cc8b
Create Date: 2026-07-08 16:27:15.265164

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7696be83c1bf'
down_revision: Union[str, None] = 'd11d9574cc8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar campos de auditoría
    op.add_column(
        'registration_attempts',
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='public'
    )
    op.add_column(
        'registration_attempts',
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        schema='public'
    )
    op.add_column(
        'registration_attempts',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        schema='public'
    )
    op.add_column(
        'registration_attempts',
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        schema='public'
    )
    
    # 2. Crear índices
    op.create_index(
        op.f('ix_public_registration_attempts_created_at'),
        'registration_attempts',
        ['created_at'],
        unique=False,
        schema='public'
    )
    op.create_index(
        op.f('ix_public_registration_attempts_created_by'),
        'registration_attempts',
        ['created_by'],
        unique=False,
        schema='public'
    )
    op.create_index(
        op.f('ix_public_registration_attempts_updated_at'),
        'registration_attempts',
        ['updated_at'],
        unique=False,
        schema='public'
    )
    op.create_index(
        op.f('ix_public_registration_attempts_updated_by'),
        'registration_attempts',
        ['updated_by'],
        unique=False,
        schema='public'
    )
    
    # 3. Agregar FKs a users (deferred)
    op.create_foreign_key(
        'fk_registration_attempts_created_by_users',
        'registration_attempts',
        'users',
        ['created_by'],
        ['id'],
        ondelete='SET NULL',
        source_schema='public',
        referent_schema='public'
    )
    op.create_foreign_key(
        'fk_registration_attempts_updated_by_users',
        'registration_attempts',
        'users',
        ['updated_by'],
        ['id'],
        ondelete='SET NULL',
        source_schema='public',
        referent_schema='public'
    )


def downgrade() -> None:
    # 1. Eliminar FKs
    op.drop_constraint(
        'fk_registration_attempts_updated_by_users',
        'registration_attempts',
        schema='public',
        type_='foreignkey'
    )
    op.drop_constraint(
        'fk_registration_attempts_created_by_users',
        'registration_attempts',
        schema='public',
        type_='foreignkey'
    )
    
    # 2. Eliminar índices
    op.drop_index(
        op.f('ix_public_registration_attempts_updated_by'),
        table_name='registration_attempts',
        schema='public'
    )
    op.drop_index(
        op.f('ix_public_registration_attempts_updated_at'),
        table_name='registration_attempts',
        schema='public'
    )
    op.drop_index(
        op.f('ix_public_registration_attempts_created_by'),
        table_name='registration_attempts',
        schema='public'
    )
    op.drop_index(
        op.f('ix_public_registration_attempts_created_at'),
        table_name='registration_attempts',
        schema='public'
    )
    
    # 3. Eliminar columnas
    op.drop_column('registration_attempts', 'updated_by', schema='public')
    op.drop_column('registration_attempts', 'updated_at', schema='public')
    op.drop_column('registration_attempts', 'created_by', schema='public')
    op.drop_column('registration_attempts', 'created_at', schema='public')
