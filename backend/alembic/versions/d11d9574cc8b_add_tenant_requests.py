"""add_tenant_requests

Revision ID: d11d9574cc8b
Revises: 06c750bb6c0c
Create Date: 2026-07-08 12:36:23.999974

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd11d9574cc8b'
down_revision: Union[str, None] = '06c750bb6c0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tenant_requests',
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('nit', sa.String(length=15), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('regimen_fiscal_id', sa.BigInteger(), nullable=True),
        sa.Column('estimated_clients_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', sa.BigInteger(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['regimen_fiscal_id'], ['public.regimenes_fiscales.id'], name='fk_tenant_requests_regimen_fiscal_id'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['public.users.id'], name='fk_tenant_requests_reviewed_by'),
        sa.PrimaryKeyConstraint('id', name='pk_tenant_requests'),
        schema='public'
    )
    op.create_index('ix_public_tenant_requests_nit', 'tenant_requests', ['nit'], unique=False, schema='public')
    op.create_index('ix_public_tenant_requests_contact_email', 'tenant_requests', ['contact_email'], unique=False, schema='public')
    op.create_index('ix_public_tenant_requests_status', 'tenant_requests', ['status'], unique=False, schema='public')
    op.create_index('ix_public_tenant_requests_public_id', 'tenant_requests', ['public_id'], unique=True, schema='public')

def downgrade() -> None:
    op.drop_index('ix_public_tenant_requests_public_id', table_name='tenant_requests', schema='public')
    op.drop_index('ix_public_tenant_requests_status', table_name='tenant_requests', schema='public')
    op.drop_index('ix_public_tenant_requests_contact_email', table_name='tenant_requests', schema='public')
    op.drop_index('ix_public_tenant_requests_nit', table_name='tenant_requests', schema='public')
    op.drop_table('tenant_requests', schema='public')