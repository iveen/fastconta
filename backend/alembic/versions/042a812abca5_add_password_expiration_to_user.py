"""add_password_expiration_to_user

Revision ID: 042a812abca5
Revises: 7696be83c1bf
Create Date: 2026-07-10 10:26:43.185828

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '042a812abca5'
down_revision: Union[str, None] = '7696be83c1bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Política de contraseñas
    op.add_column(
        'users',
        sa.Column(
            'must_change_password',
            sa.Boolean(),
            server_default='true',
            nullable=False,
            comment='Indica si el usuario debe cambiar su contraseña en el próximo login'
        ),
        schema='public'
    )
    
    op.add_column(
        'users',
        sa.Column(
            'password_changed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Fecha del último cambio de contraseña'
        ),
        schema='public'
    )
    
    op.add_column(
        'users',
        sa.Column(
            'password_expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Fecha de expiración de la contraseña (90 días)'
        ),
        schema='public'
    )
    
    # Política de bloqueo por intentos fallidos
    op.add_column(
        'users',
        sa.Column(
            'failed_login_attempts',
            sa.Integer(),
            server_default='0',
            nullable=False,
            comment='Contador de intentos fallidos consecutivos'
        ),
        schema='public'
    )
    
    op.add_column(
        'users',
        sa.Column(
            'locked_until',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Fecha hasta la cual el usuario está bloqueado'
        ),
        schema='public'
    )
    
    op.add_column(
        'users',
        sa.Column(
            'is_locked',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='Indica si el usuario está bloqueado (por intentos fallidos o admin)'
        ),
        schema='public'
    )
    
    # Índices para campos de bloqueo (útiles para queries frecuentes)
    op.create_index(
        'ix_public_users_is_locked',
        'users',
        ['is_locked'],
        schema='public'
    )
    
    op.create_index(
        'ix_public_users_must_change_password',
        'users',
        ['must_change_password'],
        schema='public'
    )


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('ix_public_users_must_change_password', table_name='users', schema='public')
    op.drop_index('ix_public_users_is_locked', table_name='users', schema='public')
    
    # Eliminar campos de bloqueo
    op.drop_column('users', 'is_locked', schema='public')
    op.drop_column('users', 'locked_until', schema='public')
    op.drop_column('users', 'failed_login_attempts', schema='public')
    
    # Eliminar campos de política de contraseñas
    op.drop_column('users', 'password_expires_at', schema='public')
    op.drop_column('users', 'password_changed_at', schema='public')
    op.drop_column('users', 'must_change_password', schema='public')