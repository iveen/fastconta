"""initial_public_schema_bigint_softdelete_audit_v3
Revision ID: 22cc9e33a26f
Revises: 
Create Date: 2026-07-07 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '22cc9e33a26f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # NIVEL 0: Tablas sin dependencias de FK
    # ============================================================
    
    # --- tenants (AuditableFull, sin FK created_by/updated_by por circularidad con users) ---
    op.create_table('tenants',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('nit', sa.String(length=15), nullable=False),
        sa.Column('schema_name', sa.String(length=63), nullable=False),
        sa.Column('admin_email', sa.String(length=255), nullable=True),
        sa.Column('plan', sa.String(length=20), nullable=False),
        sa.Column('max_empresas', sa.Integer(), nullable=False),
        sa.Column('max_usuarios', sa.Integer(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # ⚠️ FKs created_by/updated_by se agregan al final (circular con users)
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tenants')),
        sa.UniqueConstraint('nit', name=op.f('uq_tenants_nit')),
        sa.UniqueConstraint('schema_name', name=op.f('uq_tenants_schema_name')),
        schema='public'
    )
    op.create_index(op.f('ix_public_tenants_created_at'), 'tenants', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tenants_created_by'), 'tenants', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tenants_deleted_at'), 'tenants', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tenants_is_active'), 'tenants', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tenants_public_id'), 'tenants', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_tenants_updated_at'), 'tenants', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tenants_updated_by'), 'tenants', ['updated_by'], unique=False, schema='public')

    # --- roles (AuditableFull) ---
    op.create_table('roles',
        sa.Column('codigo', sa.String(length=30), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('nivel_acceso', sa.Integer(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
        schema='public'
    )
    op.create_index(op.f('ix_public_roles_codigo'), 'roles', ['codigo'], unique=True, schema='public')
    op.create_index(op.f('ix_public_roles_created_at'), 'roles', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_roles_created_by'), 'roles', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_roles_deleted_at'), 'roles', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_roles_is_active'), 'roles', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_roles_public_id'), 'roles', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_roles_updated_at'), 'roles', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_roles_updated_by'), 'roles', ['updated_by'], unique=False, schema='public')

    # --- registration_attempts (sin auditoría) ---
    op.create_table('registration_attempts',
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_registration_attempts')),
        schema='public'
    )
    op.create_index(op.f('ix_public_registration_attempts_public_id'), 'registration_attempts', ['public_id'], unique=True, schema='public')

    # --- tipos_dte (AuditableFull) ---
    op.create_table('tipos_dte',
        sa.Column('codigo', sa.String(length=10), nullable=False),
        sa.Column('descripcion', sa.String(length=100), nullable=False),
        sa.Column('requiere_complemento', sa.Boolean(), nullable=False),
        sa.Column('es_factura', sa.Boolean(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tipos_dte')),
        schema='public'
    )
    op.create_index(op.f('ix_public_tipos_dte_codigo'), 'tipos_dte', ['codigo'], unique=True, schema='public')
    op.create_index(op.f('ix_public_tipos_dte_created_at'), 'tipos_dte', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_dte_created_by'), 'tipos_dte', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_dte_deleted_at'), 'tipos_dte', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_dte_is_active'), 'tipos_dte', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_dte_public_id'), 'tipos_dte', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_tipos_dte_updated_at'), 'tipos_dte', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_dte_updated_by'), 'tipos_dte', ['updated_by'], unique=False, schema='public')

    # --- catalogo_monedas (AuditableFull) ---
    op.create_table('catalogo_monedas',
        sa.Column('codigo_banguat', sa.String(length=5), nullable=False),
        sa.Column('codigo_iso', sa.String(length=3), nullable=False),
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('simbolo', sa.String(length=5), nullable=True),
        sa.Column('decimales', sa.Integer(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_catalogo_monedas')),
        schema='public'
    )
    op.create_index(op.f('ix_public_catalogo_monedas_codigo_banguat'), 'catalogo_monedas', ['codigo_banguat'], unique=True, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_codigo_iso'), 'catalogo_monedas', ['codigo_iso'], unique=True, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_created_at'), 'catalogo_monedas', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_created_by'), 'catalogo_monedas', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_deleted_at'), 'catalogo_monedas', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_is_active'), 'catalogo_monedas', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_public_id'), 'catalogo_monedas', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_updated_at'), 'catalogo_monedas', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_monedas_updated_by'), 'catalogo_monedas', ['updated_by'], unique=False, schema='public')

    # --- catalogo_impuestos_especiales (AuditableFull) ---
    op.create_table('catalogo_impuestos_especiales',
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_catalogo_impuestos_especiales')),
        schema='public'
    )
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_codigo'), 'catalogo_impuestos_especiales', ['codigo'], unique=True, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_created_at'), 'catalogo_impuestos_especiales', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_created_by'), 'catalogo_impuestos_especiales', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_deleted_at'), 'catalogo_impuestos_especiales', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_is_active'), 'catalogo_impuestos_especiales', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_public_id'), 'catalogo_impuestos_especiales', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_updated_at'), 'catalogo_impuestos_especiales', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_especiales_updated_by'), 'catalogo_impuestos_especiales', ['updated_by'], unique=False, schema='public')

    # --- tipos_libro (AuditableFull) ---
    op.create_table('tipos_libro',
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tipos_libro')),
        sa.UniqueConstraint('nombre', name=op.f('uq_tipos_libro_nombre')),
        schema='public'
    )
    op.create_index(op.f('ix_public_tipos_libro_created_at'), 'tipos_libro', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_libro_created_by'), 'tipos_libro', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_libro_deleted_at'), 'tipos_libro', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_libro_is_active'), 'tipos_libro', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_libro_public_id'), 'tipos_libro', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_tipos_libro_updated_at'), 'tipos_libro', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_libro_updated_by'), 'tipos_libro', ['updated_by'], unique=False, schema='public')

    # --- estados_libro (AuditableFull) ---
    op.create_table('estados_libro',
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_estados_libro')),
        schema='public'
    )
    op.create_index(op.f('ix_public_estados_libro_created_at'), 'estados_libro', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_estados_libro_created_by'), 'estados_libro', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_estados_libro_deleted_at'), 'estados_libro', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_estados_libro_is_active'), 'estados_libro', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_estados_libro_public_id'), 'estados_libro', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_estados_libro_updated_at'), 'estados_libro', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_estados_libro_updated_by'), 'estados_libro', ['updated_by'], unique=False, schema='public')

    # --- tipos_persona (AuditableFull) ---
    op.create_table('tipos_persona',
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.String(length=200), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tipos_persona')),
        sa.UniqueConstraint('nombre', name=op.f('uq_tipos_persona_nombre')),
        schema='public'
    )
    op.create_index(op.f('ix_public_tipos_persona_created_at'), 'tipos_persona', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_persona_created_by'), 'tipos_persona', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_persona_deleted_at'), 'tipos_persona', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_persona_is_active'), 'tipos_persona', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_persona_public_id'), 'tipos_persona', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_tipos_persona_updated_at'), 'tipos_persona', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_persona_updated_by'), 'tipos_persona', ['updated_by'], unique=False, schema='public')

    # --- tipos_domicilio (AuditableFull) ---
    op.create_table('tipos_domicilio',
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tipos_domicilio')),
        sa.UniqueConstraint('nombre', name=op.f('uq_tipos_domicilio_nombre')),
        schema='public'
    )
    op.create_index(op.f('ix_public_tipos_domicilio_created_at'), 'tipos_domicilio', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_domicilio_created_by'), 'tipos_domicilio', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_domicilio_deleted_at'), 'tipos_domicilio', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_domicilio_is_active'), 'tipos_domicilio', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_domicilio_public_id'), 'tipos_domicilio', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_tipos_domicilio_updated_at'), 'tipos_domicilio', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_tipos_domicilio_updated_by'), 'tipos_domicilio', ['updated_by'], unique=False, schema='public')

    # --- departamentos (AuditableFull) ---
    op.create_table('departamentos',
        sa.Column('codigo_iso', sa.String(length=2), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_departamentos')),
        sa.UniqueConstraint('codigo_iso', name=op.f('uq_departamentos_codigo_iso')),
        schema='public'
    )
    op.create_index(op.f('ix_public_departamentos_created_at'), 'departamentos', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_departamentos_created_by'), 'departamentos', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_departamentos_deleted_at'), 'departamentos', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_departamentos_is_active'), 'departamentos', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_departamentos_public_id'), 'departamentos', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_departamentos_updated_at'), 'departamentos', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_departamentos_updated_by'), 'departamentos', ['updated_by'], unique=False, schema='public')

    # --- actividades_economicas_sat (AuditableFull) ---
    op.create_table('actividades_economicas_sat',
        sa.Column('codigo_sat', sa.String(length=20), nullable=False),
        sa.Column('nombre_actividad', sa.String(length=255), nullable=False),
        sa.Column('seccion', sa.String(length=255), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_actividades_economicas_sat')),
        schema='public'
    )
    op.create_index(op.f('ix_public_actividades_economicas_sat_codigo_sat'), 'actividades_economicas_sat', ['codigo_sat'], unique=True, schema='public')
    op.create_index(op.f('ix_public_actividades_economicas_sat_created_at'), 'actividades_economicas_sat', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_actividades_economicas_sat_created_by'), 'actividades_economicas_sat', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_actividades_economicas_sat_deleted_at'), 'actividades_economicas_sat', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_actividades_economicas_sat_is_active'), 'actividades_economicas_sat', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_actividades_economicas_sat_public_id'), 'actividades_economicas_sat', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_actividades_economicas_sat_updated_at'), 'actividades_economicas_sat', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_actividades_economicas_sat_updated_by'), 'actividades_economicas_sat', ['updated_by'], unique=False, schema='public')

    # --- categorias_activos_fijos (AuditableFull) ---
    op.create_table('categorias_activos_fijos',
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('tasa_minima_anual', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('tasa_maxima_anual', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('vida_util_meses_default', sa.Integer(), nullable=False),
        sa.Column('codigo_prefijo', sa.String(length=10), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.CheckConstraint('tasa_maxima_anual >= tasa_minima_anual', name=op.f('ck_categorias_activos_fijos_chk_categoria_tasa_valida')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_categorias_activos_fijos')),
        sa.UniqueConstraint('nombre', name=op.f('uq_categorias_activos_fijos_nombre')),
        schema='public'
    )
    op.create_index(op.f('ix_public_categorias_activos_fijos_codigo_prefijo'), 'categorias_activos_fijos', ['codigo_prefijo'], unique=True, schema='public')
    op.create_index(op.f('ix_public_categorias_activos_fijos_created_at'), 'categorias_activos_fijos', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_categorias_activos_fijos_created_by'), 'categorias_activos_fijos', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_categorias_activos_fijos_deleted_at'), 'categorias_activos_fijos', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_categorias_activos_fijos_is_active'), 'categorias_activos_fijos', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_categorias_activos_fijos_public_id'), 'categorias_activos_fijos', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_categorias_activos_fijos_updated_at'), 'categorias_activos_fijos', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_categorias_activos_fijos_updated_by'), 'categorias_activos_fijos', ['updated_by'], unique=False, schema='public')

    # --- regimenes_fiscales (AuditableFull) ---
    op.create_table('regimenes_fiscales',
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_regimenes_fiscales')),
        schema='public'
    )
    op.create_index(op.f('ix_public_regimenes_fiscales_codigo'), 'regimenes_fiscales', ['codigo'], unique=True, schema='public')
    op.create_index(op.f('ix_public_regimenes_fiscales_created_at'), 'regimenes_fiscales', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_fiscales_created_by'), 'regimenes_fiscales', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_fiscales_deleted_at'), 'regimenes_fiscales', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_fiscales_is_active'), 'regimenes_fiscales', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_fiscales_public_id'), 'regimenes_fiscales', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_regimenes_fiscales_updated_at'), 'regimenes_fiscales', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_fiscales_updated_by'), 'regimenes_fiscales', ['updated_by'], unique=False, schema='public')

    # --- catalogo_impuestos (AuditableFull) ---
    op.create_table('catalogo_impuestos',
        sa.Column('codigo', sa.String(length=20), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('tasa_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('tasa_fija_monto', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_inferior', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_superior', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('frecuencia_pago', sa.String(length=20), nullable=False),
        sa.Column('frecuencia_liquidacion', sa.String(length=20), nullable=False),
        sa.Column('es_acreditable', sa.Boolean(), nullable=False),
        sa.Column('requiere_autorizacion_sat', sa.Boolean(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_catalogo_impuestos')),
        schema='public'
    )
    op.create_index(op.f('ix_public_catalogo_impuestos_codigo'), 'catalogo_impuestos', ['codigo'], unique=True, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_created_at'), 'catalogo_impuestos', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_created_by'), 'catalogo_impuestos', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_deleted_at'), 'catalogo_impuestos', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_is_active'), 'catalogo_impuestos', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_public_id'), 'catalogo_impuestos', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_updated_at'), 'catalogo_impuestos', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_catalogo_impuestos_updated_by'), 'catalogo_impuestos', ['updated_by'], unique=False, schema='public')

    # --- formularios_sat (AuditableFull, auto-referencia) ---
    op.create_table('formularios_sat',
        sa.Column('codigo', sa.String(length=20), nullable=False),
        sa.Column('version', sa.String(length=10), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('fecha_vigencia_desde', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.Column('fecha_vigencia_hasta', sa.Date(), nullable=True),
        sa.Column('es_version_activa', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('editable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('formulario_padre_id', sa.BigInteger(), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # ✅ FK auto-referencia SÍ se incluye (no es circular con users)
        sa.ForeignKeyConstraint(['formulario_padre_id'], ['public.formularios_sat.id'], name=op.f('fk_formularios_sat_formulario_padre_id_formularios_sat')),
        # ⚠️ FKs created_by/updated_by se agregan al final
        sa.PrimaryKeyConstraint('id', name=op.f('pk_formularios_sat')),
        sa.UniqueConstraint('codigo', 'version', name='uq_formulario_codigo_version'),
        schema='public'
    )
    op.create_index('idx_formularios_vigencia', 'formularios_sat', ['codigo', 'fecha_vigencia_desde', 'fecha_vigencia_hasta'], unique=False, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_codigo'), 'formularios_sat', ['codigo'], unique=False, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_created_at'), 'formularios_sat', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_created_by'), 'formularios_sat', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_deleted_at'), 'formularios_sat', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_is_active'), 'formularios_sat', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_public_id'), 'formularios_sat', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_updated_at'), 'formularios_sat', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_formularios_sat_updated_by'), 'formularios_sat', ['updated_by'], unique=False, schema='public')

    # ============================================================
    # NIVEL 1: Dependen del nivel 0
    # ============================================================
    
    # --- users (AuditableFull, depende de tenants y roles) ---
    op.create_table('users',
        sa.Column('tenant_id', sa.BigInteger(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.BigInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # ✅ FKs a tenants y roles SÍ se incluyen
        sa.ForeignKeyConstraint(['role_id'], ['public.roles.id'], name=op.f('fk_users_role_id_roles')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], name=op.f('fk_users_tenant_id_tenants')),
        # ⚠️ FK created_by se agrega al final (auto-referencia)
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        schema='public'
    )
    op.create_index(op.f('ix_public_users_created_at'), 'users', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_users_created_by'), 'users', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_users_deleted_at'), 'users', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_users_email'), 'users', ['email'], unique=True, schema='public')
    op.create_index(op.f('ix_public_users_is_active'), 'users', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_users_public_id'), 'users', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_users_updated_at'), 'users', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_users_updated_by'), 'users', ['updated_by'], unique=False, schema='public')

    # --- municipios (AuditableFull, depende de departamentos) ---
    op.create_table('municipios',
        sa.Column('codigo_iso', sa.String(length=4), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('departamento_id', sa.BigInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['departamento_id'], ['public.departamentos.id'], name=op.f('fk_municipios_departamento_id_departamentos')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_municipios')),
        sa.UniqueConstraint('codigo_iso', name=op.f('uq_municipios_codigo_iso')),
        schema='public'
    )
    op.create_index(op.f('ix_public_municipios_created_at'), 'municipios', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_municipios_created_by'), 'municipios', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_municipios_deleted_at'), 'municipios', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_municipios_is_active'), 'municipios', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_municipios_public_id'), 'municipios', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_municipios_updated_at'), 'municipios', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_municipios_updated_by'), 'municipios', ['updated_by'], unique=False, schema='public')

    # --- secciones_formulario (AuditableFull, depende de formularios_sat) ---
    op.create_table('secciones_formulario',
        sa.Column('formulario_id', sa.BigInteger(), nullable=False),
        sa.Column('numero_seccion', sa.String(length=10), nullable=False),
        sa.Column('titulo', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.Column('tipo_seccion', sa.String(length=30), nullable=False),
        sa.Column('es_obligatoria', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('requiere_exportador', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('es_automatica', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['formulario_id'], ['public.formularios_sat.id'], name=op.f('fk_secciones_formulario_formulario_id_formularios_sat')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_secciones_formulario')),
        sa.UniqueConstraint('formulario_id', 'numero_seccion', name='uq_seccion_formulario'),
        schema='public'
    )
    op.create_index(op.f('ix_public_secciones_formulario_created_at'), 'secciones_formulario', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_secciones_formulario_created_by'), 'secciones_formulario', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_secciones_formulario_deleted_at'), 'secciones_formulario', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_secciones_formulario_is_active'), 'secciones_formulario', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_secciones_formulario_public_id'), 'secciones_formulario', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_secciones_formulario_updated_at'), 'secciones_formulario', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_secciones_formulario_updated_by'), 'secciones_formulario', ['updated_by'], unique=False, schema='public')

    # --- regimen_dte_config (AuditableFull, depende de regimenes_fiscales y tipos_dte) ---
    op.create_table('regimen_dte_config',
        sa.Column('regimen_id', sa.BigInteger(), nullable=False),
        sa.Column('dte_id', sa.BigInteger(), nullable=False),
        sa.Column('es_exclusivo', sa.Boolean(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['dte_id'], ['public.tipos_dte.id'], name=op.f('fk_regimen_dte_config_dte_id_tipos_dte')),
        sa.ForeignKeyConstraint(['regimen_id'], ['public.regimenes_fiscales.id'], name=op.f('fk_regimen_dte_config_regimen_id_regimenes_fiscales')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_regimen_dte_config')),
        schema='public'
    )
    op.create_index(op.f('ix_public_regimen_dte_config_created_at'), 'regimen_dte_config', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_dte_config_created_by'), 'regimen_dte_config', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_dte_config_deleted_at'), 'regimen_dte_config', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_dte_config_is_active'), 'regimen_dte_config', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_dte_config_public_id'), 'regimen_dte_config', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_regimen_dte_config_updated_at'), 'regimen_dte_config', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_dte_config_updated_by'), 'regimen_dte_config', ['updated_by'], unique=False, schema='public')

    # --- regimen_impuesto_config (AuditableFull, depende de regimenes_fiscales y catalogo_impuestos) ---
    op.create_table('regimen_impuesto_config',
        sa.Column('regimen_id', sa.BigInteger(), nullable=False),
        sa.Column('impuesto_id', sa.BigInteger(), nullable=False),
        sa.Column('tasa_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('tasa_fija_monto', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_inferior', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_superior', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('es_acreditable', sa.Boolean(), nullable=False),
        sa.Column('es_retencion_definitiva', sa.Boolean(), nullable=False),
        sa.Column('requiere_autorizacion_sat', sa.Boolean(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['impuesto_id'], ['public.catalogo_impuestos.id'], name=op.f('fk_regimen_impuesto_config_impuesto_id_catalogo_impuestos')),
        sa.ForeignKeyConstraint(['regimen_id'], ['public.regimenes_fiscales.id'], name=op.f('fk_regimen_impuesto_config_regimen_id_regimenes_fiscales')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_regimen_impuesto_config')),
        sa.UniqueConstraint('regimen_id', 'impuesto_id', name='uq_regimen_impuesto_unico'),
        schema='public'
    )
    op.create_index(op.f('ix_public_regimen_impuesto_config_created_at'), 'regimen_impuesto_config', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_created_by'), 'regimen_impuesto_config', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_deleted_at'), 'regimen_impuesto_config', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_impuesto_id'), 'regimen_impuesto_config', ['impuesto_id'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_is_active'), 'regimen_impuesto_config', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_public_id'), 'regimen_impuesto_config', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_regimen_id'), 'regimen_impuesto_config', ['regimen_id'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_updated_at'), 'regimen_impuesto_config', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimen_impuesto_config_updated_by'), 'regimen_impuesto_config', ['updated_by'], unique=False, schema='public')

    # --- regimenes_formularios_sat (AuditableFull, depende de regimenes_fiscales y formularios_sat) ---
    op.create_table('regimenes_formularios_sat',
        sa.Column('regimen_id', sa.BigInteger(), nullable=False),
        sa.Column('formulario_id', sa.BigInteger(), nullable=False),
        sa.Column('es_obligatorio', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['formulario_id'], ['public.formularios_sat.id'], name=op.f('fk_regimenes_formularios_sat_formulario_id_formularios_sat')),
        sa.ForeignKeyConstraint(['regimen_id'], ['public.regimenes_fiscales.id'], name=op.f('fk_regimenes_formularios_sat_regimen_id_regimenes_fiscales')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_regimenes_formularios_sat')),
        sa.UniqueConstraint('regimen_id', 'formulario_id', name='uq_regimen_formulario'),
        schema='public'
    )
    op.create_index(op.f('ix_public_regimenes_formularios_sat_created_at'), 'regimenes_formularios_sat', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_formularios_sat_created_by'), 'regimenes_formularios_sat', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_formularios_sat_deleted_at'), 'regimenes_formularios_sat', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_formularios_sat_is_active'), 'regimenes_formularios_sat', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_formularios_sat_public_id'), 'regimenes_formularios_sat', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_regimenes_formularios_sat_updated_at'), 'regimenes_formularios_sat', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_regimenes_formularios_sat_updated_by'), 'regimenes_formularios_sat', ['updated_by'], unique=False, schema='public')

    # --- user_empresas (AuditableFull, depende de users y tenants) ---
    op.create_table('user_empresas',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], name=op.f('fk_user_empresas_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], name=op.f('fk_user_empresas_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_empresas')),
        sa.UniqueConstraint('user_id', 'tenant_id', 'empresa_id', name='uq_user_empresa_tenant'),
        schema='public'
    )
    op.create_index(op.f('ix_public_user_empresas_created_at'), 'user_empresas', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_user_empresas_created_by'), 'user_empresas', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_user_empresas_deleted_at'), 'user_empresas', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_user_empresas_is_active'), 'user_empresas', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_user_empresas_public_id'), 'user_empresas', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_user_empresas_updated_at'), 'user_empresas', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_user_empresas_updated_by'), 'user_empresas', ['updated_by'], unique=False, schema='public')

    # ============================================================
    # NIVEL 2: Dependen del nivel 1
    # ============================================================
    
    # --- casillas_sat (AuditableFull, depende de secciones_formulario) ---
    op.create_table('casillas_sat',
        sa.Column('seccion_id', sa.BigInteger(), nullable=True),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('codigo_visual', sa.String(length=20), nullable=True),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('orden_seccion', sa.Integer(), nullable=True),
        sa.Column('tipo_casilla', sa.String(length=30), nullable=False),
        sa.Column('naturaleza', sa.String(length=20), nullable=True),
        sa.Column('formula_calculo', sa.Text(), nullable=True),
        sa.Column('porcentaje_aplicable', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('campo_origen_factura', sa.String(length=50), nullable=True),
        sa.Column('es_editable', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('requiere_justificacion', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('es_visible_usuario', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('es_automatica', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('dependencias', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('funcion_calculo', sa.String(length=50), nullable=True),
        sa.Column('parametros_funcion', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['seccion_id'], ['public.secciones_formulario.id'], name=op.f('fk_casillas_sat_seccion_id_secciones_formulario')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_casillas_sat')),
        sa.UniqueConstraint('seccion_id', 'codigo', name='uq_casilla_seccion_codigo'),
        schema='public'
    )
    op.create_index(op.f('ix_public_casillas_sat_created_at'), 'casillas_sat', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_casillas_sat_created_by'), 'casillas_sat', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_casillas_sat_deleted_at'), 'casillas_sat', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_casillas_sat_is_active'), 'casillas_sat', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_casillas_sat_public_id'), 'casillas_sat', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_casillas_sat_updated_at'), 'casillas_sat', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_casillas_sat_updated_by'), 'casillas_sat', ['updated_by'], unique=False, schema='public')

    # ============================================================
    # NIVEL 3: Dependen del nivel 2
    # ============================================================
    
    # --- exclusiones_casilla (AuditableFull, depende de casillas_sat) ---
    op.create_table('exclusiones_casilla',
        sa.Column('casilla_id', sa.BigInteger(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('criterios_exclusion_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['casilla_id'], ['public.casillas_sat.id'], name=op.f('fk_exclusiones_casilla_casilla_id_casillas_sat')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_exclusiones_casilla')),
        schema='public'
    )
    op.create_index(op.f('ix_public_exclusiones_casilla_created_at'), 'exclusiones_casilla', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_exclusiones_casilla_created_by'), 'exclusiones_casilla', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_exclusiones_casilla_deleted_at'), 'exclusiones_casilla', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_exclusiones_casilla_is_active'), 'exclusiones_casilla', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_exclusiones_casilla_public_id'), 'exclusiones_casilla', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_exclusiones_casilla_updated_at'), 'exclusiones_casilla', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_exclusiones_casilla_updated_by'), 'exclusiones_casilla', ['updated_by'], unique=False, schema='public')

    # --- reglas_filtrado_factura (AuditableFull, depende de casillas_sat) ---
    op.create_table('reglas_filtrado_factura',
        sa.Column('casilla_id', sa.BigInteger(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('criterios_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('campo_factura', sa.String(length=50), nullable=False),
        sa.Column('operacion', sa.String(length=20), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['casilla_id'], ['public.casillas_sat.id'], name=op.f('fk_reglas_filtrado_factura_casilla_id_casillas_sat')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_reglas_filtrado_factura')),
        schema='public'
    )
    op.create_index(op.f('ix_public_reglas_filtrado_factura_created_at'), 'reglas_filtrado_factura', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_reglas_filtrado_factura_created_by'), 'reglas_filtrado_factura', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_reglas_filtrado_factura_deleted_at'), 'reglas_filtrado_factura', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_reglas_filtrado_factura_is_active'), 'reglas_filtrado_factura', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_reglas_filtrado_factura_public_id'), 'reglas_filtrado_factura', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_reglas_filtrado_factura_updated_at'), 'reglas_filtrado_factura', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_reglas_filtrado_factura_updated_by'), 'reglas_filtrado_factura', ['updated_by'], unique=False, schema='public')

    # --- mapeo_casilla_cuenta (AuditableFull, depende de casillas_sat y tenants) ---
    op.create_table('mapeo_casilla_cuenta',
        sa.Column('casilla_id', sa.BigInteger(), nullable=False),
        sa.Column('tenant_id', sa.BigInteger(), nullable=True),
        sa.Column('empresa_id', sa.BigInteger(), nullable=True),
        sa.Column('codigo_cuenta_sugerido', sa.String(length=20), nullable=False),
        sa.Column('nombre_cuenta_sugerido', sa.String(length=255), nullable=False),
        sa.Column('tipo_movimiento', sa.String(length=10), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['casilla_id'], ['public.casillas_sat.id'], name=op.f('fk_mapeo_casilla_cuenta_casilla_id_casillas_sat')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], name=op.f('fk_mapeo_casilla_cuenta_tenant_id_tenants')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mapeo_casilla_cuenta')),
        sa.UniqueConstraint('casilla_id', 'tenant_id', 'empresa_id', name='uq_casilla_tenant_empresa'),
        schema='public'
    )
    op.create_index(op.f('ix_public_mapeo_casilla_cuenta_created_at'), 'mapeo_casilla_cuenta', ['created_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_mapeo_casilla_cuenta_created_by'), 'mapeo_casilla_cuenta', ['created_by'], unique=False, schema='public')
    op.create_index(op.f('ix_public_mapeo_casilla_cuenta_deleted_at'), 'mapeo_casilla_cuenta', ['deleted_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_mapeo_casilla_cuenta_is_active'), 'mapeo_casilla_cuenta', ['is_active'], unique=False, schema='public')
    op.create_index(op.f('ix_public_mapeo_casilla_cuenta_public_id'), 'mapeo_casilla_cuenta', ['public_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_mapeo_casilla_cuenta_updated_at'), 'mapeo_casilla_cuenta', ['updated_at'], unique=False, schema='public')
    op.create_index(op.f('ix_public_mapeo_casilla_cuenta_updated_by'), 'mapeo_casilla_cuenta', ['updated_by'], unique=False, schema='public')

    # ============================================================
    # AGREGAR FKs DIFERIDAS (created_by/updated_by → users.id)
    # ============================================================
    
    # TODAS las tablas con auditoría (ahora todas son AuditableFull)
    tablas_auditable_full = [
        'tenants', 'roles', 'tipos_dte', 'catalogo_monedas', 'catalogo_impuestos_especiales',
        'tipos_libro', 'estados_libro', 'tipos_persona', 'tipos_domicilio',
        'departamentos', 'municipios', 'actividades_economicas_sat',
        'categorias_activos_fijos', 'regimenes_fiscales', 'catalogo_impuestos',
        'formularios_sat', 'users', 'secciones_formulario',
        'regimen_dte_config', 'regimen_impuesto_config', 'regimenes_formularios_sat',
        'user_empresas', 'casillas_sat', 'exclusiones_casilla',
        'reglas_filtrado_factura', 'mapeo_casilla_cuenta'
    ]
    
    for tabla in tablas_auditable_full:
        schema = 'public'
        op.create_foreign_key(
            f'fk_{tabla}_created_by_users',
            tabla, 'users',
            ['created_by'], ['id'],
            ondelete='SET NULL',
            source_schema=schema,
            referent_schema='public'
        )
        op.create_foreign_key(
            f'fk_{tabla}_updated_by_users',
            tabla, 'users',
            ['updated_by'], ['id'],
            ondelete='SET NULL',
            source_schema=schema,
            referent_schema='public'
        )


def downgrade() -> None:
    # ============================================================
    # ELIMINAR FKs DIFERIDAS (en orden inverso)
    # ============================================================
    
    # TODAS las tablas con auditoría (ahora todas son AuditableFull)
    tablas_auditable_full = [
        'tenants', 'roles', 'tipos_dte', 'catalogo_monedas', 'catalogo_impuestos_especiales',
        'tipos_libro', 'estados_libro', 'tipos_persona', 'tipos_domicilio',
        'departamentos', 'municipios', 'actividades_economicas_sat',
        'categorias_activos_fijos', 'regimenes_fiscales', 'catalogo_impuestos',
        'formularios_sat', 'users', 'secciones_formulario',
        'regimen_dte_config', 'regimen_impuesto_config', 'regimenes_formularios_sat',
        'user_empresas', 'casillas_sat', 'exclusiones_casilla',
        'reglas_filtrado_factura', 'mapeo_casilla_cuenta'
    ]
    
    for tabla in tablas_auditable_full:
        schema = 'public'
        op.drop_constraint(f'fk_{tabla}_updated_by_users', tabla, schema=schema, type_='foreignkey')
        op.drop_constraint(f'fk_{tabla}_created_by_users', tabla, schema=schema, type_='foreignkey')
    
    # ============================================================
    # ELIMINAR TABLAS (en orden inverso al upgrade)
    # ============================================================
    
    # Nivel 3
    op.drop_table('mapeo_casilla_cuenta', schema='public')
    op.drop_table('reglas_filtrado_factura', schema='public')
    op.drop_table('exclusiones_casilla', schema='public')
    
    # Nivel 2
    op.drop_table('casillas_sat', schema='public')
    
    # Nivel 1
    op.drop_table('user_empresas', schema='public')
    op.drop_table('regimenes_formularios_sat', schema='public')
    op.drop_table('regimen_impuesto_config', schema='public')
    op.drop_table('regimen_dte_config', schema='public')
    op.drop_table('secciones_formulario', schema='public')
    op.drop_table('municipios', schema='public')
    op.drop_table('users', schema='public')
    
    # Nivel 0
    op.drop_table('formularios_sat', schema='public')
    op.drop_table('catalogo_impuestos', schema='public')
    op.drop_table('regimenes_fiscales', schema='public')
    op.drop_table('categorias_activos_fijos', schema='public')
    op.drop_table('actividades_economicas_sat', schema='public')
    op.drop_table('departamentos', schema='public')
    op.drop_table('tipos_domicilio', schema='public')
    op.drop_table('tipos_persona', schema='public')
    op.drop_table('estados_libro', schema='public')
    op.drop_table('tipos_libro', schema='public')
    op.drop_table('catalogo_impuestos_especiales', schema='public')
    op.drop_table('catalogo_monedas', schema='public')
    op.drop_table('tipos_dte', schema='public')
    op.drop_table('registration_attempts', schema='public')
    op.drop_table('roles', schema='public')
    op.drop_table('tenants', schema='public')