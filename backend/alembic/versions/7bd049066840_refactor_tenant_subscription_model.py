"""refactor_tenant_subscription_model
Revision ID: 7bd049066840
Revises: b218b1aceccf
Create Date: 2026-07-26 13:44:08.844089
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '7bd049066840'
down_revision: Union[str, None] = 'b218b1aceccf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name, column_name, schema='public'):
    """Helper para verificar si una columna existe"""
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_schema = :schema 
            AND table_name = :table 
            AND column_name = :column
        )
    """), {"schema": schema, "table": table_name, "column": column_name})
    return result.scalar()


def table_exists(table_name, schema='public'):
    """Helper para verificar si una tabla existe"""
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = :schema 
            AND table_name = :table
        )
    """), {"schema": schema, "table": table_name})
    return result.scalar()


def upgrade() -> None:
    # ============================================================
    # 1. MODIFICAR TABLA TENANTS
    # ============================================================
    
    # Agregar nuevas columnas (si no existen)
    if not column_exists('tenants', 'max_concurrent_sessions'):
        op.add_column('tenants', sa.Column('max_concurrent_sessions', sa.Integer(), nullable=False, server_default='1'))
    
    if not column_exists('tenants', 'max_users_registered'):
        op.add_column('tenants', sa.Column('max_users_registered', sa.Integer(), nullable=False, server_default='3'))
    
    # Migrar datos existentes: max_usuarios -> max_users_registered
    if column_exists('tenants', 'max_usuarios'):
        op.execute("""
            UPDATE tenants 
            SET max_users_registered = max_usuarios 
            WHERE max_usuarios IS NOT NULL
        """)
    
    # Crear índice para plan (si no existe)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename = 'tenants' 
            AND indexname = 'ix_tenants_plan'
        )
    """))
    if not result.scalar():
        op.create_index('ix_tenants_plan', 'tenants', ['plan'])
    
    # Eliminar columnas antiguas de trial (si existen)
    if column_exists('tenants', 'trial_max_usuarios'):
        op.drop_column('tenants', 'trial_max_usuarios')
    
    if column_exists('tenants', 'trial_until'):
        op.drop_column('tenants', 'trial_until')
    
    if column_exists('tenants', 'max_usuarios'):
        op.drop_column('tenants', 'max_usuarios')
    
    # ============================================================
    # 2. CREAR TABLA TENANT_SUBSCRIPTIONS (si no existe)
    # ============================================================
    if not table_exists('tenant_subscriptions'):
        op.create_table(
            'tenant_subscriptions',
            sa.Column('id', sa.BigInteger(), nullable=False),
            sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
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
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('created_by', sa.BigInteger(), nullable=True),
            sa.Column('updated_by', sa.BigInteger(), nullable=True),
            sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by'], ['public.users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['updated_by'], ['public.users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('public_id'),
            sa.UniqueConstraint('tenant_id', 'current_period_start', name='uq_tenant_active_subscription'),
            schema='public'
        )
        
        # Índices para tenant_subscriptions
        op.create_index('idx_tenant_subscriptions_tenant', 'tenant_subscriptions', ['tenant_id'], schema='public')
        op.create_index('idx_tenant_subscriptions_status', 'tenant_subscriptions', ['status'], schema='public')
        op.create_index('idx_tenant_subscriptions_period', 'tenant_subscriptions', ['current_period_start', 'current_period_end'], schema='public')
        op.create_index('ix_tenant_subscriptions_public_id', 'tenant_subscriptions', ['public_id'], unique=True, schema='public')
        op.create_index('ix_tenant_subscriptions_created_by', 'tenant_subscriptions', ['created_by'], schema='public')
        op.create_index('ix_tenant_subscriptions_updated_by', 'tenant_subscriptions', ['updated_by'], schema='public')
    else:
        # La tabla ya existe, agregar columnas faltantes
        if not column_exists('tenant_subscriptions', 'public_id'):
            op.add_column('tenant_subscriptions', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
            op.create_index('ix_tenant_subscriptions_public_id', 'tenant_subscriptions', ['public_id'], unique=True, schema='public')
        
        if not column_exists('tenant_subscriptions', 'created_by'):
            op.add_column('tenant_subscriptions', sa.Column('created_by', sa.BigInteger(), nullable=True))
            op.create_foreign_key('fk_tenant_subscriptions_created_by_users', 'tenant_subscriptions', 'users', ['created_by'], ['id'], source_schema='public', referent_schema='public', ondelete='SET NULL')
            op.create_index('ix_tenant_subscriptions_created_by', 'tenant_subscriptions', ['created_by'], schema='public')
        
        if not column_exists('tenant_subscriptions', 'updated_by'):
            op.add_column('tenant_subscriptions', sa.Column('updated_by', sa.BigInteger(), nullable=True))
            op.create_foreign_key('fk_tenant_subscriptions_updated_by_users', 'tenant_subscriptions', 'users', ['updated_by'], ['id'], source_schema='public', referent_schema='public', ondelete='SET NULL')
            op.create_index('ix_tenant_subscriptions_updated_by', 'tenant_subscriptions', ['updated_by'], schema='public')
    
    # ============================================================
    # 3. CREAR TABLA SUBSCRIPTION_USAGE_LOGS (si no existe)
    # ============================================================
    if not table_exists('subscription_usage_logs'):
        op.create_table(
            'subscription_usage_logs',
            sa.Column('id', sa.BigInteger(), nullable=False),
            sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
            sa.Column('subscription_id', sa.BigInteger(), nullable=False),
            sa.Column('concurrent_sessions_used', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_users_registered', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('peak_concurrent_sessions', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('logged_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('session_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('created_by', sa.BigInteger(), nullable=True),
            sa.Column('updated_by', sa.BigInteger(), nullable=True),
            sa.ForeignKeyConstraint(['subscription_id'], ['public.tenant_subscriptions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by'], ['public.users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['updated_by'], ['public.users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('public_id'),
            schema='public'
        )
        
        op.create_index('idx_usage_logs_subscription', 'subscription_usage_logs', ['subscription_id'], schema='public')
        op.create_index('idx_usage_logs_date', 'subscription_usage_logs', ['logged_at'], schema='public')
        op.create_index('ix_subscription_usage_logs_public_id', 'subscription_usage_logs', ['public_id'], unique=True, schema='public')
        op.create_index('ix_subscription_usage_logs_created_by', 'subscription_usage_logs', ['created_by'], schema='public')
        op.create_index('ix_subscription_usage_logs_updated_by', 'subscription_usage_logs', ['updated_by'], schema='public')
    else:
        # Agregar columnas faltantes
        if not column_exists('subscription_usage_logs', 'public_id'):
            op.add_column('subscription_usage_logs', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
            op.create_index('ix_subscription_usage_logs_public_id', 'subscription_usage_logs', ['public_id'], unique=True, schema='public')
        
        if not column_exists('subscription_usage_logs', 'created_at'):
            op.add_column('subscription_usage_logs', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
        
        if not column_exists('subscription_usage_logs', 'updated_at'):
            op.add_column('subscription_usage_logs', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
        
        if not column_exists('subscription_usage_logs', 'created_by'):
            op.add_column('subscription_usage_logs', sa.Column('created_by', sa.BigInteger(), nullable=True))
            op.create_foreign_key('fk_subscription_usage_logs_created_by_users', 'subscription_usage_logs', 'users', ['created_by'], ['id'], source_schema='public', referent_schema='public', ondelete='SET NULL')
            op.create_index('ix_subscription_usage_logs_created_by', 'subscription_usage_logs', ['created_by'], schema='public')
        
        if not column_exists('subscription_usage_logs', 'updated_by'):
            op.add_column('subscription_usage_logs', sa.Column('updated_by', sa.BigInteger(), nullable=True))
            op.create_foreign_key('fk_subscription_usage_logs_updated_by_users', 'subscription_usage_logs', 'users', ['updated_by'], ['id'], source_schema='public', referent_schema='public', ondelete='SET NULL')
            op.create_index('ix_subscription_usage_logs_updated_by', 'subscription_usage_logs', ['updated_by'], schema='public')
    
    # ============================================================
    # 4. CREAR TABLA SESSION_AUDIT (si no existe)
    # ============================================================
    if not table_exists('session_audit'):
        op.create_table(
            'session_audit',
            sa.Column('id', sa.BigInteger(), nullable=False),
            sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
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
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('created_by', sa.BigInteger(), nullable=True),
            sa.Column('updated_by', sa.BigInteger(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by'], ['public.users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['updated_by'], ['public.users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('public_id'),
            sa.UniqueConstraint('session_token'),
            schema='public'
        )
        
        op.create_index('idx_session_audit_user', 'session_audit', ['user_id'], schema='public')
        op.create_index('idx_session_audit_tenant', 'session_audit', ['tenant_id'], schema='public')
        op.create_index('idx_session_audit_session', 'session_audit', ['session_token'], unique=True, schema='public')
        op.create_index('idx_session_audit_active', 'session_audit', ['is_active', 'last_activity'], schema='public')
        op.create_index('ix_session_audit_public_id', 'session_audit', ['public_id'], unique=True, schema='public')
        op.create_index('ix_session_audit_created_by', 'session_audit', ['created_by'], schema='public')
        op.create_index('ix_session_audit_updated_by', 'session_audit', ['updated_by'], schema='public')
    else:
        # Agregar columnas faltantes
        if not column_exists('session_audit', 'public_id'):
            op.add_column('session_audit', sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')))
            op.create_index('ix_session_audit_public_id', 'session_audit', ['public_id'], unique=True, schema='public')
        
        if not column_exists('session_audit', 'updated_at'):
            op.add_column('session_audit', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
        
        if not column_exists('session_audit', 'created_by'):
            op.add_column('session_audit', sa.Column('created_by', sa.BigInteger(), nullable=True))
            op.create_foreign_key('fk_session_audit_created_by_users', 'session_audit', 'users', ['created_by'], ['id'], source_schema='public', referent_schema='public', ondelete='SET NULL')
            op.create_index('ix_session_audit_created_by', 'session_audit', ['created_by'], schema='public')
        
        if not column_exists('session_audit', 'updated_by'):
            op.add_column('session_audit', sa.Column('updated_by', sa.BigInteger(), nullable=True))
            op.create_foreign_key('fk_session_audit_updated_by_users', 'session_audit', 'users', ['updated_by'], ['id'], source_schema='public', referent_schema='public', ondelete='SET NULL')
            op.create_index('ix_session_audit_updated_by', 'session_audit', ['updated_by'], schema='public')
    
    # ============================================================
    # 5. MIGRAR DATOS: CREAR SUSCRIPCIONES INICIALES
    # ============================================================
    # Solo si la tabla tenant_subscriptions está vacía
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM public.tenant_subscriptions"))
    count = result.scalar()
    
    if count == 0:
        op.execute("""
            INSERT INTO public.tenant_subscriptions (
                tenant_id, plan_type, max_concurrent_sessions, max_users_registered,
                price_per_user, base_price, total_monthly_price, billing_cycle,
                current_period_start, current_period_end, status, billing_email
            )
            SELECT 
                id,
                COALESCE(plan, 'freemium'),
                1,
                max_users_registered,
                0.00,
                0.00,
                0.00,
                'mensual',
                NOW(),
                NOW() + INTERVAL '365 days',
                'activa',
                admin_email
            FROM public.tenants
            WHERE schema_name NOT IN ('sistema', 'system', 'public')
        """)


def downgrade() -> None:
    # ============================================================
    # 1. ELIMINAR TABLAS NUEVAS (en orden inverso de dependencias)
    # ============================================================
    if table_exists('session_audit'):
        op.drop_table('session_audit', schema='public')
    
    if table_exists('subscription_usage_logs'):
        op.drop_table('subscription_usage_logs', schema='public')
    
    if table_exists('tenant_subscriptions'):
        op.drop_table('tenant_subscriptions', schema='public')
    
    # ============================================================
    # 2. RESTAURAR TABLA TENANTS
    # ============================================================
    # Agregar columnas antiguas de vuelta
    if not column_exists('tenants', 'max_usuarios'):
        op.add_column('tenants', sa.Column('max_usuarios', sa.Integer(), nullable=False, server_default='3'))
    
    if not column_exists('tenants', 'trial_until'):
        op.add_column('tenants', sa.Column('trial_until', sa.DateTime(timezone=True), nullable=True))
    
    if not column_exists('tenants', 'trial_max_usuarios'):
        op.add_column('tenants', sa.Column('trial_max_usuarios', sa.Integer(), nullable=True))
    
    # Migrar datos de vuelta
    if column_exists('tenants', 'max_users_registered') and column_exists('tenants', 'max_usuarios'):
        op.execute("""
            UPDATE tenants 
            SET max_usuarios = max_users_registered
        """)
    
    # Eliminar índice de plan
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename = 'tenants' 
            AND indexname = 'ix_tenants_plan'
        )
    """))
    if result.scalar():
        op.drop_index('ix_tenants_plan', table_name='tenants')
    
    # Eliminar nuevas columnas
    if column_exists('tenants', 'max_users_registered'):
        op.drop_column('tenants', 'max_users_registered')
    
    if column_exists('tenants', 'max_concurrent_sessions'):
        op.drop_column('tenants', 'max_concurrent_sessions')
