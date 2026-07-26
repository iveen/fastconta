"""refactor_tenant_subscription_model
Revision ID: 7bd049066840
Revises: b218b1aceccf
Create Date: 2026-07-26 13:44:08.844089
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7bd049066840'
down_revision: Union[str, None] = 'b218b1aceccf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # 1. MODIFICAR TABLA TENANTS
    # ============================================================
    
    # Agregar nuevas columnas
    op.add_column('tenants', sa.Column('max_concurrent_sessions', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('tenants', sa.Column('max_users_registered', sa.Integer(), nullable=False, server_default='3'))
    
    # Migrar datos existentes: max_usuarios -> max_users_registered
    op.execute("""
        UPDATE tenants 
        SET max_users_registered = max_usuarios 
        WHERE max_usuarios IS NOT NULL
    """)
    
    # Crear índice para plan
    op.create_index('ix_tenants_plan', 'tenants', ['plan'])
    
    # Eliminar columnas antiguas de trial
    op.drop_column('tenants', 'trial_max_usuarios')
    op.drop_column('tenants', 'trial_until')
    op.drop_column('tenants', 'max_usuarios')
    
    # ============================================================
    # 2. CREAR TABLA TENANT_SUBSCRIPTIONS
    # ============================================================
    op.create_table(
        'tenant_subscriptions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('plan_type', sa.String(length=20), nullable=False),
        sa.Column('max_concurrent_sessions', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_users_registered', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price_per_user', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('base_price', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_monthly_price', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('billing_cycle', sa.String(length=20), nullable=False, server_default='mensual'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='prueba'),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('last_payment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_payment_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_email', sa.String(length=255), nullable=True),
        sa.Column('billing_address', sa.Text(), nullable=True),
        sa.Column('nit_facturacion', sa.String(length=15), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'current_period_start', name='uq_tenant_active_subscription'),
        schema='public'
    )
    
    # Índices para tenant_subscriptions
    op.create_index('idx_tenant_subscriptions_tenant', 'tenant_subscriptions', ['tenant_id'], schema='public')
    op.create_index('idx_tenant_subscriptions_status', 'tenant_subscriptions', ['status'], schema='public')
    op.create_index('idx_tenant_subscriptions_period', 'tenant_subscriptions', ['current_period_start', 'current_period_end'], schema='public')
    
    # ============================================================
    # 3. CREAR TABLA SUBSCRIPTION_USAGE_LOGS
    # ============================================================
    op.create_table(
        'subscription_usage_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('subscription_id', sa.BigInteger(), nullable=False),
        sa.Column('concurrent_sessions_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_users_registered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('peak_concurrent_sessions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('logged_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('session_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['public.tenant_subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # Índices para subscription_usage_logs
    op.create_index('idx_usage_logs_subscription', 'subscription_usage_logs', ['subscription_id'], schema='public')
    op.create_index('idx_usage_logs_date', 'subscription_usage_logs', ['logged_at'], schema='public')
    
    # ============================================================
    # 4. CREAR TABLA SESSION_AUDIT
    # ============================================================
    op.create_table(
        'session_audit',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('session_token', sa.String(length=500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('login_method', sa.String(length=20), nullable=True),
        sa.Column('logout_reason', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token'),
        schema='public'
    )
    
    # Índices para session_audit
    op.create_index('idx_session_audit_user', 'session_audit', ['user_id'], schema='public')
    op.create_index('idx_session_audit_tenant', 'session_audit', ['tenant_id'], schema='public')
    op.create_index('idx_session_audit_session', 'session_audit', ['session_token'], unique=True, schema='public')
    op.create_index('idx_session_audit_active', 'session_audit', ['is_active', 'last_activity'], schema='public')
    
    # ============================================================
    # 5. MIGRAR DATOS: CREAR SUSCRIPCIONES INICIALES
    # ============================================================
    op.execute("""
        INSERT INTO public.tenant_subscriptions (
            tenant_id, plan_type, max_concurrent_sessions, max_users_registered,
            price_per_user, base_price, total_monthly_price, billing_cycle,
            current_period_start, current_period_end, status, billing_email
        )
        SELECT 
            id,
            COALESCE(plan, 'freemium'),
            1,  -- max_concurrent_sessions default
            max_users_registered,
            0.00,  -- price_per_user
            0.00,  -- base_price
            0.00,  -- total_monthly_price
            'mensual',  -- billing_cycle
            NOW(),  -- current_period_start
            NOW() + INTERVAL '365 days',  -- current_period_end (1 año de gracia)
            'activa',  -- status
            admin_email  -- billing_email
        FROM public.tenants
        WHERE schema_name NOT IN ('sistema', 'system', 'public')
    """)


def downgrade() -> None:
    # ============================================================
    # 1. ELIMINAR TABLAS NUEVAS
    # ============================================================
    op.drop_table('session_audit', schema='public')
    op.drop_table('subscription_usage_logs', schema='public')
    op.drop_table('tenant_subscriptions', schema='public')
    
    # ============================================================
    # 2. RESTAURAR TABLA TENANTS
    # ============================================================
    
    # Agregar columnas antiguas de vuelta
    op.add_column('tenants', sa.Column('max_usuarios', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('tenants', sa.Column('trial_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tenants', sa.Column('trial_max_usuarios', sa.Integer(), nullable=True))
    
    # Migrar datos de vuelta: max_users_registered -> max_usuarios
    op.execute("""
        UPDATE tenants 
        SET max_usuarios = max_users_registered
    """)
    
    # Eliminar índice de plan
    op.drop_index('ix_tenants_plan', table_name='tenants')
    
    # Eliminar nuevas columnas
    op.drop_column('tenants', 'max_users_registered')
    op.drop_column('tenants', 'max_concurrent_sessions')
