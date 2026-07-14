"""add_login_audit_password_reset

Revision ID: 057ab6f6f99b
Revises: 042a812abca5
Create Date: 2026-07-13 09:32:55.196034

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '057ab6f6f99b'
down_revision: Union[str, None] = '042a812abca5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # Tabla: login_audit
    # ============================================================
    op.create_table(
        'login_audit',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('email_attempted', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), nullable=False,
                  comment='SUCCESS, FAILED_INVALID_PASSWORD, FAILED_LOCKED, FAILED_USER_NOT_FOUND'),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
        schema='public',
    )
    op.create_index('ix_login_audit_user_id', 'login_audit', ['user_id'], schema='public')
    op.create_index('ix_login_audit_email_attempted', 'login_audit', ['email_attempted'], schema='public')
    op.create_index('ix_login_audit_created_at', 'login_audit', ['created_at'], schema='public')

    # ============================================================
    # Tabla: password_reset_tokens
    # ============================================================
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False,
                  comment='Hash del token por seguridad'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
        sa.UniqueConstraint('token_hash'),
        schema='public',
    )
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'], schema='public')
    op.create_index('ix_password_reset_tokens_token_hash', 'password_reset_tokens', ['token_hash'], schema='public')
    op.create_index('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'], schema='public')


def downgrade() -> None:
    # ============================================================
    # Eliminar password_reset_tokens
    # ============================================================
    op.drop_index('ix_password_reset_tokens_expires_at', table_name='password_reset_tokens', schema='public')
    op.drop_index('ix_password_reset_tokens_token_hash', table_name='password_reset_tokens', schema='public')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens', schema='public')
    op.drop_table('password_reset_tokens', schema='public')

    # ============================================================
    # Eliminar login_audit
    # ============================================================
    op.drop_index('ix_login_audit_created_at', table_name='login_audit', schema='public')
    op.drop_index('ix_login_audit_email_attempted', table_name='login_audit', schema='public')
    op.drop_index('ix_login_audit_user_id', table_name='login_audit', schema='public')
    op.drop_table('login_audit', schema='public')
