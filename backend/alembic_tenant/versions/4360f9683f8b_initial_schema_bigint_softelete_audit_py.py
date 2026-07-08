"""initial_schema_bigint,softelete_audit.py

Revision ID: 4360f9683f8b
Revises: 
Create Date: 2026-07-07 09:34:55.352149

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4360f9683f8b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """
    Crea todas las tablas del schema del tenant.
    Esta migración se ejecuta dinámicamente cuando se crea un nuevo tenant.
    
    IMPORTANTE: Las tablas NO tienen schema='public' explícito.
    Se asume que se crean en el schema del tenant actual (search_path).
    
    Las FKs a tablas globales usan 'public.tabla.id' explícitamente.
    Las FKs de auditoría (created_by/updated_by) se agregan al final.
    """
    
    # ============================================================
    # NIVEL 0: Empresa (depende de tablas public que ya existen)
    # ============================================================
    
    # --- empresas (AuditableFull, SoftDelete) ---
    op.create_table('empresas',
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('razon_social', sa.String(length=255), nullable=True),
        sa.Column('nombre_comercial', sa.String(length=255), nullable=True),
        sa.Column('nit', sa.String(length=20), nullable=False),
        sa.Column('fecha_constitucion', sa.Date(), nullable=True),
        sa.Column('clave_ingreso', sa.Text(), nullable=True),
        sa.Column('direccion', sa.Text(), nullable=True),
        sa.Column('regimen_fiscal_id', sa.BigInteger(), nullable=True),
        sa.Column('tipo_persona_id', sa.BigInteger(), nullable=True),
        sa.Column('actividad_economica_id', sa.BigInteger(), nullable=True),
        sa.Column('cuenta_utilidad_periodo_id', sa.BigInteger(), nullable=True),
        sa.Column('cuenta_utilidades_acumuladas_id', sa.BigInteger(), nullable=True),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # SoftDelete
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Indica si el registro está activo (soft delete)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Fecha y hora en que el registro fue eliminado (soft delete)'),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # ✅ FKs a tablas public (ya existen)
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], name=op.f('fk_empresas_tenant_id_tenants')),
        sa.ForeignKeyConstraint(['regimen_fiscal_id'], ['public.regimenes_fiscales.id'], name=op.f('fk_empresas_regimen_fiscal_id_regimenes_fiscales')),
        sa.ForeignKeyConstraint(['tipo_persona_id'], ['public.tipos_persona.id'], name=op.f('fk_empresas_tipo_persona_id_tipos_persona')),
        sa.ForeignKeyConstraint(['actividad_economica_id'], ['public.actividades_economicas_sat.id'], name=op.f('fk_empresas_actividad_economica_id_actividades_economicas_sat')),
        # ⚠️ FKs a plan_cuentas se agregan después (dependencia circular)
        # ⚠️ FKs created_by/updated_by se agregan al final
        sa.PrimaryKeyConstraint('id', name=op.f('pk_empresas')),
        sa.UniqueConstraint('nit', name=op.f('uq_empresas_nit'))
    )
    op.create_index(op.f('ix_empresas_created_at'), 'empresas', ['created_at'], unique=False)
    op.create_index(op.f('ix_empresas_created_by'), 'empresas', ['created_by'], unique=False)
    op.create_index(op.f('ix_empresas_deleted_at'), 'empresas', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_empresas_is_active'), 'empresas', ['is_active'], unique=False)
    op.create_index(op.f('ix_empresas_public_id'), 'empresas', ['public_id'], unique=True)
    op.create_index(op.f('ix_empresas_tenant_id'), 'empresas', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_empresas_updated_at'), 'empresas', ['updated_at'], unique=False)
    op.create_index(op.f('ix_empresas_updated_by'), 'empresas', ['updated_by'], unique=False)

    # ============================================================
    # NIVEL 1: Dependen de Empresa
    # ============================================================
    
    # --- domicilios (AuditableFull, SoftDelete) ---
    op.create_table('domicilios',
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('tipo_domicilio_id', sa.BigInteger(), nullable=False),
        sa.Column('departamento_id', sa.BigInteger(), nullable=False),
        sa.Column('municipio_id', sa.BigInteger(), nullable=False),
        sa.Column('direccion_exacta', sa.String(length=255), nullable=False),
        sa.Column('zona', sa.String(length=10), nullable=True),
        sa.Column('codigo_postal', sa.String(length=10), nullable=True),
        # BIGINT PK + public_id
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
        # ✅ FKs a tablas public
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_domicilios_empresa_id_empresas')),
        sa.ForeignKeyConstraint(['tipo_domicilio_id'], ['public.tipos_domicilio.id'], name=op.f('fk_domicilios_tipo_domicilio_id_tipos_domicilio')),
        sa.ForeignKeyConstraint(['departamento_id'], ['public.departamentos.id'], name=op.f('fk_domicilios_departamento_id_departamentos')),
        sa.ForeignKeyConstraint(['municipio_id'], ['public.municipios.id'], name=op.f('fk_domicilios_municipio_id_municipios')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_domicilios'))
    )
    op.create_index(op.f('ix_domicilios_created_at'), 'domicilios', ['created_at'], unique=False)
    op.create_index(op.f('ix_domicilios_created_by'), 'domicilios', ['created_by'], unique=False)
    op.create_index(op.f('ix_domicilios_deleted_at'), 'domicilios', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_domicilios_is_active'), 'domicilios', ['is_active'], unique=False)
    op.create_index(op.f('ix_domicilios_public_id'), 'domicilios', ['public_id'], unique=True)
    op.create_index(op.f('ix_domicilios_updated_at'), 'domicilios', ['updated_at'], unique=False)
    op.create_index(op.f('ix_domicilios_updated_by'), 'domicilios', ['updated_by'], unique=False)

    # --- representantes_legales (AuditableFull, SoftDelete) ---
    op.create_table('representantes_legales',
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('dpi', sa.String(length=20), nullable=False),
        sa.Column('fecha_nombramiento', sa.Date(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        # BIGINT PK + public_id
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
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_representantes_legales_empresa_id_empresas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_representantes_legales'))
    )
    op.create_index(op.f('ix_representantes_legales_created_at'), 'representantes_legales', ['created_at'], unique=False)
    op.create_index(op.f('ix_representantes_legales_created_by'), 'representantes_legales', ['created_by'], unique=False)
    op.create_index(op.f('ix_representantes_legales_deleted_at'), 'representantes_legales', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_representantes_legales_is_active'), 'representantes_legales', ['is_active'], unique=False)
    op.create_index(op.f('ix_representantes_legales_public_id'), 'representantes_legales', ['public_id'], unique=True)
    op.create_index(op.f('ix_representantes_legales_updated_at'), 'representantes_legales', ['updated_at'], unique=False)
    op.create_index(op.f('ix_representantes_legales_updated_by'), 'representantes_legales', ['updated_by'], unique=False)

    # --- plan_cuentas (AuditableFull, SoftDelete, auto-referencia) ---
    op.create_table('plan_cuentas',
        sa.Column('codigo', sa.String(length=20), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('naturaleza', sa.String(length=10), nullable=False),
        sa.Column('acepta_tercero', sa.Boolean(), nullable=True),
        sa.Column('nivel', sa.Integer(), nullable=True),
        sa.Column('cuenta_padre_id', sa.BigInteger(), nullable=True),
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        # BIGINT PK + public_id
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
        # ✅ FK auto-referencia (no es circular con users)
        sa.ForeignKeyConstraint(['cuenta_padre_id'], ['plan_cuentas.id'], name=op.f('fk_plan_cuentas_cuenta_padre_id_plan_cuentas')),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_plan_cuentas_empresa_id_empresas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_plan_cuentas')),
        sa.UniqueConstraint('codigo', 'empresa_id', name='plan_cuentas_codigo_empresa_unique')
    )
    op.create_index(op.f('ix_plan_cuentas_codigo'), 'plan_cuentas', ['codigo'], unique=False)
    op.create_index(op.f('ix_plan_cuentas_created_at'), 'plan_cuentas', ['created_at'], unique=False)
    op.create_index(op.f('ix_plan_cuentas_created_by'), 'plan_cuentas', ['created_by'], unique=False)
    op.create_index(op.f('ix_plan_cuentas_deleted_at'), 'plan_cuentas', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_plan_cuentas_is_active'), 'plan_cuentas', ['is_active'], unique=False)
    op.create_index(op.f('ix_plan_cuentas_public_id'), 'plan_cuentas', ['public_id'], unique=True)
    op.create_index(op.f('ix_plan_cuentas_updated_at'), 'plan_cuentas', ['updated_at'], unique=False)
    op.create_index(op.f('ix_plan_cuentas_updated_by'), 'plan_cuentas', ['updated_by'], unique=False)

    # --- secuencias (sin auditoría) ---
    op.create_table('secuencias',
        sa.Column('entidad', sa.String(length=50), nullable=False),
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('contador', sa.Integer(), nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_secuencias_empresa_id_empresas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_secuencias')),
        sa.UniqueConstraint('entidad', 'empresa_id', name='uq_secuencias_entidad_empresa')
    )
    op.create_index(op.f('ix_secuencias_public_id'), 'secuencias', ['public_id'], unique=True)

    # --- periodos_fiscales (AuditableFull) ---
    op.create_table('periodos_fiscales',
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('fecha_fin', sa.Date(), nullable=False),
        sa.Column('cerrado', sa.Boolean(), nullable=False),
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_periodos_fiscales_empresa_id_empresas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_periodos_fiscales'))
    )
    op.create_index(op.f('ix_periodos_fiscales_created_at'), 'periodos_fiscales', ['created_at'], unique=False)
    op.create_index(op.f('ix_periodos_fiscales_created_by'), 'periodos_fiscales', ['created_by'], unique=False)
    op.create_index(op.f('ix_periodos_fiscales_public_id'), 'periodos_fiscales', ['public_id'], unique=True)
    op.create_index(op.f('ix_periodos_fiscales_updated_at'), 'periodos_fiscales', ['updated_at'], unique=False)
    op.create_index(op.f('ix_periodos_fiscales_updated_by'), 'periodos_fiscales', ['updated_by'], unique=False)

    # ============================================================
    # NIVEL 2: Dependen de Empresa y Nivel 1
    # ============================================================
    
    # --- partidas (AuditableFull, auto-referencia) ---
    op.create_table('partidas',
        sa.Column('numero_poliza', sa.String(length=50), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('fue_revertida', sa.Boolean(), nullable=True),
        sa.Column('partida_reversion_id', sa.BigInteger(), nullable=True),
        sa.Column('tipo_origen', sa.String(length=50), nullable=False),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # ✅ FK auto-referencia
        sa.ForeignKeyConstraint(['partida_reversion_id'], ['partidas.id'], name=op.f('fk_partidas_partida_reversion_id_partidas')),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_partidas_empresa_id_empresas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_partidas'))
    )
    op.create_index(op.f('ix_partidas_created_at'), 'partidas', ['created_at'], unique=False)
    op.create_index(op.f('ix_partidas_created_by'), 'partidas', ['created_by'], unique=False)
    op.create_index(op.f('ix_partidas_empresa_id'), 'partidas', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_partidas_fecha'), 'partidas', ['fecha'], unique=False)
    op.create_index(op.f('ix_partidas_public_id'), 'partidas', ['public_id'], unique=True)
    op.create_index(op.f('ix_partidas_updated_at'), 'partidas', ['updated_at'], unique=False)
    op.create_index(op.f('ix_partidas_updated_by'), 'partidas', ['updated_by'], unique=False)

    # --- facturas_electronicas (AuditableFull) ---
    op.create_table('facturas_electronicas',
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('xml_original', sa.Text(), nullable=False),
        sa.Column('xml_filename', sa.String(length=255), nullable=True),
        sa.Column('numero_autorizacion', sa.String(length=50), nullable=False),
        sa.Column('autorizacion_uuid', sa.String(length=50), nullable=True),
        sa.Column('serie', sa.String(length=20), nullable=True),
        sa.Column('numero', sa.String(length=20), nullable=False),
        sa.Column('tipo_documento', sa.String(length=10), nullable=True),
        sa.Column('moneda', sa.String(length=5), nullable=True),
        sa.Column('retencion_iva', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True),
        sa.Column('retencion_isr', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True),
        sa.Column('clasificacion_gasto_sat', sa.String(length=50), server_default='NORMAL', nullable=True),
        sa.Column('es_importacion', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('requiere_revision_manual', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('tipo_documento_id', sa.BigInteger(), nullable=True),
        sa.Column('moneda_id', sa.BigInteger(), nullable=True),
        sa.Column('fecha_emision', sa.DateTime(timezone=True), nullable=False),
        sa.Column('emisor_nit', sa.String(length=15), nullable=False),
        sa.Column('emisor_nombre', sa.String(length=255), nullable=False),
        sa.Column('receptor_nit', sa.String(length=15), nullable=False),
        sa.Column('receptor_nombre', sa.String(length=255), nullable=False),
        sa.Column('total_exento', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_gravado', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_iva', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tipo_cambio', sa.Numeric(precision=10, scale=5), nullable=True),
        sa.Column('total_gravado_gtq', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_iva_gtq', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_exento_gtq', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_gtq', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_gravado_bienes', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_iva_bienes', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_gravado_servicios', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_iva_servicios', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_gravado_bienes_gtq', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_iva_bienes_gtq', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_gravado_servicios_gtq', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_iva_servicios_gtq', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('es_exportacion', sa.Boolean(), nullable=True),
        sa.Column('pais_destino_exportacion', sa.String(length=100), nullable=True),
        sa.Column('nombre_comercial', sa.String(length=255), nullable=True),
        sa.Column('tipo_operacion', sa.String(length=10), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('fecha_anulacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validado', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('fecha_validacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # ✅ FKs a tablas public
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_facturas_electronicas_empresa_id_empresas')),
        sa.ForeignKeyConstraint(['tipo_documento_id'], ['public.tipos_dte.id'], name=op.f('fk_facturas_electronicas_tipo_documento_id_tipos_dte')),
        sa.ForeignKeyConstraint(['moneda_id'], ['public.catalogo_monedas.id'], name=op.f('fk_facturas_electronicas_moneda_id_catalogo_monedas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_facturas_electronicas'))
    )
    op.create_index(op.f('ix_facturas_electronicas_created_by'), 'facturas_electronicas', ['created_by'], unique=False)
    op.create_index(op.f('ix_facturas_electronicas_empresa_id'), 'facturas_electronicas', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_facturas_electronicas_fecha_emision'), 'facturas_electronicas', ['fecha_emision'], unique=False)
    op.create_index(op.f('ix_facturas_electronicas_moneda_id'), 'facturas_electronicas', ['moneda_id'], unique=False)
    op.create_index(op.f('ix_facturas_electronicas_public_id'), 'facturas_electronicas', ['public_id'], unique=True)
    op.create_index(op.f('ix_facturas_electronicas_tipo_documento_id'), 'facturas_electronicas', ['tipo_documento_id'], unique=False)
    op.create_index(op.f('ix_facturas_electronicas_updated_at'), 'facturas_electronicas', ['updated_at'], unique=False)
    op.create_index(op.f('ix_facturas_electronicas_updated_by'), 'facturas_electronicas', ['updated_by'], unique=False)

    # --- sat_libros (AuditableFull) ---
    op.create_table('sat_libros',
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('tipo_libro_id', sa.BigInteger(), nullable=False),
        sa.Column('regimen_fiscal_id', sa.BigInteger(), nullable=False),
        sa.Column('estado_id', sa.BigInteger(), nullable=False),
        sa.Column('anio_periodo', sa.SmallInteger(), nullable=False),
        sa.Column('mes_periodo', sa.SmallInteger(), nullable=False),
        sa.Column('total_lineas', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_exento', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('total_base_imponible', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('total_iva', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('total_monto', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('finalizado_por', sa.BigInteger(), nullable=True),
        sa.Column('finalizado_el', sa.DateTime(timezone=True), nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # ✅ FKs a tablas public
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_sat_libros_empresa_id_empresas'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tipo_libro_id'], ['public.tipos_libro.id'], name=op.f('fk_sat_libros_tipo_libro_id_tipos_libro')),
        sa.ForeignKeyConstraint(['regimen_fiscal_id'], ['public.regimenes_fiscales.id'], name=op.f('fk_sat_libros_regimen_fiscal_id_regimenes_fiscales')),
        sa.ForeignKeyConstraint(['estado_id'], ['public.estados_libro.id'], name=op.f('fk_sat_libros_estado_id_estados_libro')),
        sa.CheckConstraint('mes_periodo BETWEEN 1 AND 12', name=op.f('ck_sat_libros_chk_sat_libros_mes_periodo')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sat_libros')),
        sa.UniqueConstraint('empresa_id', 'tipo_libro_id', 'regimen_fiscal_id', 'anio_periodo', 'mes_periodo', name='uq_sat_libros_periodo')
    )
    op.create_index('idx_sat_libros_empresa_periodo', 'sat_libros', ['empresa_id', 'anio_periodo', 'mes_periodo'], unique=False)
    op.create_index(op.f('ix_sat_libros_created_at'), 'sat_libros', ['created_at'], unique=False)
    op.create_index(op.f('ix_sat_libros_created_by'), 'sat_libros', ['created_by'], unique=False)
    op.create_index(op.f('ix_sat_libros_public_id'), 'sat_libros', ['public_id'], unique=True)
    op.create_index(op.f('ix_sat_libros_updated_at'), 'sat_libros', ['updated_at'], unique=False)
    op.create_index(op.f('ix_sat_libros_updated_by'), 'sat_libros', ['updated_by'], unique=False)

    # --- activos_fijos (AuditableFull, SoftDelete) ---
    op.create_table('activos_fijos',
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('categoria_id', sa.BigInteger(), nullable=False),
        sa.Column('codigo_interno', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=False),
        sa.Column('fecha_adquisicion', sa.Date(), nullable=False),
        sa.Column('valor_costo', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('valor_residual', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('tasa_depreciacion_anual_aplicada', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('vida_util_meses_aplicada', sa.Integer(), nullable=False),
        sa.Column('cuenta_gasto_id', sa.BigInteger(), nullable=True),
        sa.Column('cuenta_depreciacion_acumulada_id', sa.BigInteger(), nullable=True),
        sa.Column('estado', sa.String(length=30), nullable=False),
        # BIGINT PK + public_id
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
        # ✅ FKs
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_activos_fijos_empresa_id_empresas')),
        sa.ForeignKeyConstraint(['categoria_id'], ['public.categorias_activos_fijos.id'], name=op.f('fk_activos_fijos_categoria_id_categorias_activos_fijos')),
        # ⚠️ FKs a plan_cuentas se agregan después
        sa.CheckConstraint('tasa_depreciacion_anual_aplicada >= 0 AND tasa_depreciacion_anual_aplicada <= 100', name=op.f('ck_activos_fijos_chk_activos_fijos_tasa_valida')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activos_fijos'))
    )
    op.create_index(op.f('ix_activos_fijos_created_at'), 'activos_fijos', ['created_at'], unique=False)
    op.create_index(op.f('ix_activos_fijos_created_by'), 'activos_fijos', ['created_by'], unique=False)
    op.create_index(op.f('ix_activos_fijos_deleted_at'), 'activos_fijos', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_activos_fijos_empresa_id'), 'activos_fijos', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_activos_fijos_is_active'), 'activos_fijos', ['is_active'], unique=False)
    op.create_index(op.f('ix_activos_fijos_public_id'), 'activos_fijos', ['public_id'], unique=True)
    op.create_index(op.f('ix_activos_fijos_updated_at'), 'activos_fijos', ['updated_at'], unique=False)
    op.create_index(op.f('ix_activos_fijos_updated_by'), 'activos_fijos', ['updated_by'], unique=False)

    # --- declaraciones_impuesto (AuditableFull) ---
    op.create_table('declaraciones_impuesto',
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('formulario_sat_id', sa.BigInteger(), nullable=False),
        sa.Column('anio', sa.SmallInteger(), nullable=False),
        sa.Column('mes', sa.SmallInteger(), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('total_debito_fiscal', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('total_credito_fiscal', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('impuesto_determinado', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('remanente_periodo_anterior', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('remanente_siguiente_periodo', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('impuesto_a_pagar', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('finalizado_por', sa.BigInteger(), nullable=True),
        sa.Column('fecha_cierre', sa.DateTime(timezone=True), nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        # ✅ FKs
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_declaraciones_impuesto_empresa_id_empresas')),
        sa.ForeignKeyConstraint(['formulario_sat_id'], ['public.formularios_sat.id'], name=op.f('fk_declaraciones_impuesto_formulario_sat_id_formularios_sat')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_declaraciones_impuesto')),
        sa.UniqueConstraint('empresa_id', 'formulario_sat_id', 'anio', 'mes', name='uq_declaracion_periodo')
    )
    op.create_index(op.f('ix_declaraciones_impuesto_anio'), 'declaraciones_impuesto', ['anio'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_created_at'), 'declaraciones_impuesto', ['created_at'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_created_by'), 'declaraciones_impuesto', ['created_by'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_empresa_id'), 'declaraciones_impuesto', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_mes'), 'declaraciones_impuesto', ['mes'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_public_id'), 'declaraciones_impuesto', ['public_id'], unique=True)
    op.create_index(op.f('ix_declaraciones_impuesto_updated_at'), 'declaraciones_impuesto', ['updated_at'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_updated_by'), 'declaraciones_impuesto', ['updated_by'], unique=False)

    # ============================================================
    # NIVEL 3: Dependen de Nivel 2
    # ============================================================
    
    # --- detalle_partidas (AuditableFull) ---
    op.create_table('detalle_partidas',
        sa.Column('partida_id', sa.BigInteger(), nullable=False),
        sa.Column('cuenta_id', sa.BigInteger(), nullable=False),
        sa.Column('tipo_movimiento', sa.String(length=10), nullable=False),
        sa.Column('monto', sa.Numeric(precision=12, scale=2), nullable=False),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['partida_id'], ['partidas.id'], name=op.f('fk_detalle_partidas_partida_id_partidas'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cuenta_id'], ['plan_cuentas.id'], name=op.f('fk_detalle_partidas_cuenta_id_plan_cuentas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_detalle_partidas'))
    )
    op.create_index(op.f('ix_detalle_partidas_created_at'), 'detalle_partidas', ['created_at'], unique=False)
    op.create_index(op.f('ix_detalle_partidas_created_by'), 'detalle_partidas', ['created_by'], unique=False)
    op.create_index(op.f('ix_detalle_partidas_cuenta_id'), 'detalle_partidas', ['cuenta_id'], unique=False)
    op.create_index(op.f('ix_detalle_partidas_partida_id'), 'detalle_partidas', ['partida_id'], unique=False)
    op.create_index(op.f('ix_detalle_partidas_public_id'), 'detalle_partidas', ['public_id'], unique=True)
    op.create_index(op.f('ix_detalle_partidas_updated_at'), 'detalle_partidas', ['updated_at'], unique=False)
    op.create_index(op.f('ix_detalle_partidas_updated_by'), 'detalle_partidas', ['updated_by'], unique=False)

    # --- factura_detalles (AuditableFull) ---
    op.create_table('factura_detalles',
        sa.Column('factura_id', sa.BigInteger(), nullable=False),
        sa.Column('cantidad', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('descripcion', sa.String(length=500), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_linea', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('iva_linea', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('precio_unitario_gtq', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_linea_gtq', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('iva_linea_gtq', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('bien_o_servicio', sa.String(length=1), server_default='B', nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['factura_id'], ['facturas_electronicas.id'], name=op.f('fk_factura_detalles_factura_id_facturas_electronicas'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_factura_detalles'))
    )
    op.create_index(op.f('ix_factura_detalles_created_at'), 'factura_detalles', ['created_at'], unique=False)
    op.create_index(op.f('ix_factura_detalles_created_by'), 'factura_detalles', ['created_by'], unique=False)
    op.create_index(op.f('ix_factura_detalles_factura_id'), 'factura_detalles', ['factura_id'], unique=False)
    op.create_index(op.f('ix_factura_detalles_public_id'), 'factura_detalles', ['public_id'], unique=True)
    op.create_index(op.f('ix_factura_detalles_updated_at'), 'factura_detalles', ['updated_at'], unique=False)
    op.create_index(op.f('ix_factura_detalles_updated_by'), 'factura_detalles', ['updated_by'], unique=False)

    # --- facturas_impuestos_especiales (AuditableFull) ---
    op.create_table('facturas_impuestos_especiales',
        sa.Column('factura_id', sa.BigInteger(), nullable=False),
        sa.Column('catalogo_id', sa.BigInteger(), nullable=False),
        sa.Column('monto', sa.Numeric(precision=12, scale=2), server_default='0', nullable=False),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['factura_id'], ['facturas_electronicas.id'], name=op.f('fk_facturas_impuestos_especiales_factura_id_facturas_electronicas')),
        sa.ForeignKeyConstraint(['catalogo_id'], ['public.catalogo_impuestos_especiales.id'], name=op.f('fk_facturas_impuestos_especiales_catalogo_id_catalogo_impuestos_especiales')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_facturas_impuestos_especiales'))
    )
    op.create_index(op.f('ix_facturas_impuestos_especiales_catalogo_id'), 'facturas_impuestos_especiales', ['catalogo_id'], unique=False)
    op.create_index(op.f('ix_facturas_impuestos_especiales_created_at'), 'facturas_impuestos_especiales', ['created_at'], unique=False)
    op.create_index(op.f('ix_facturas_impuestos_especiales_created_by'), 'facturas_impuestos_especiales', ['created_by'], unique=False)
    op.create_index(op.f('ix_facturas_impuestos_especiales_factura_id'), 'facturas_impuestos_especiales', ['factura_id'], unique=False)
    op.create_index(op.f('ix_facturas_impuestos_especiales_public_id'), 'facturas_impuestos_especiales', ['public_id'], unique=True)
    op.create_index(op.f('ix_facturas_impuestos_especiales_updated_at'), 'facturas_impuestos_especiales', ['updated_at'], unique=False)
    op.create_index(op.f('ix_facturas_impuestos_especiales_updated_by'), 'facturas_impuestos_especiales', ['updated_by'], unique=False)

    # --- sat_libros_lineas (AuditableFull) ---
    op.create_table('sat_libros_lineas',
        sa.Column('libro_id', sa.BigInteger(), nullable=False),
        sa.Column('factura_id', sa.BigInteger(), nullable=False),
        sa.Column('numero_secuencia', sa.Integer(), nullable=False),
        sa.Column('fecha_documento', sa.Date(), nullable=False),
        sa.Column('numero_documento', sa.String(length=50), nullable=False),
        sa.Column('nit', sa.String(length=20), nullable=True),
        sa.Column('razon_social', sa.String(length=255), nullable=True),
        sa.Column('es_exento', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('es_exonerado', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('base_imponible', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('monto_exento', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('monto_iva', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('monto_total', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('credito_fiscal', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('debito_fiscal', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['libro_id'], ['sat_libros.id'], name=op.f('fk_sat_libros_lineas_libro_id_sat_libros'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sat_libros_lineas')),
        sa.UniqueConstraint('libro_id', 'numero_secuencia', name='uq_sat_libros_lineas_secuencia')
    )
    op.create_index('idx_sat_libros_lineas_libro', 'sat_libros_lineas', ['libro_id'], unique=False)
    op.create_index(op.f('ix_sat_libros_lineas_created_at'), 'sat_libros_lineas', ['created_at'], unique=False)
    op.create_index(op.f('ix_sat_libros_lineas_created_by'), 'sat_libros_lineas', ['created_by'], unique=False)
    op.create_index(op.f('ix_sat_libros_lineas_libro_id'), 'sat_libros_lineas', ['libro_id'], unique=False)
    op.create_index(op.f('ix_sat_libros_lineas_public_id'), 'sat_libros_lineas', ['public_id'], unique=True)
    op.create_index(op.f('ix_sat_libros_lineas_updated_at'), 'sat_libros_lineas', ['updated_at'], unique=False)
    op.create_index(op.f('ix_sat_libros_lineas_updated_by'), 'sat_libros_lineas', ['updated_by'], unique=False)

    # --- depreciacion_activos (AuditableFull) ---
    op.create_table('depreciacion_activos',
        sa.Column('empresa_id', sa.BigInteger(), nullable=False),
        sa.Column('activo_id', sa.BigInteger(), nullable=False),
        sa.Column('anio_periodo', sa.SmallInteger(), nullable=False),
        sa.Column('mes_periodo', sa.SmallInteger(), nullable=False),
        sa.Column('monto_depreciacion_mes', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('depreciacion_acumulada_hasta_fecha', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('valor_en_libros', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('partida_id', sa.BigInteger(), nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['activo_id'], ['activos_fijos.id'], name=op.f('fk_depreciacion_activos_activo_id_activos_fijos')),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_depreciacion_activos_empresa_id_empresas')),
        sa.ForeignKeyConstraint(['partida_id'], ['partidas.id'], name=op.f('fk_depreciacion_activos_partida_id_partidas')),
        sa.CheckConstraint('mes_periodo BETWEEN 1 AND 12', name=op.f('ck_depreciacion_activos_chk_depreciacion_mes_valido')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_depreciacion_activos')),
        sa.UniqueConstraint('activo_id', 'anio_periodo', 'mes_periodo', name='uq_depreciacion_activo_periodo')
    )
    op.create_index('idx_depreciacion_activos_empresa_periodo', 'depreciacion_activos', ['empresa_id', 'anio_periodo', 'mes_periodo'], unique=False)
    op.create_index(op.f('ix_depreciacion_activos_created_at'), 'depreciacion_activos', ['created_at'], unique=False)
    op.create_index(op.f('ix_depreciacion_activos_created_by'), 'depreciacion_activos', ['created_by'], unique=False)
    op.create_index(op.f('ix_depreciacion_activos_empresa_id'), 'depreciacion_activos', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_depreciacion_activos_public_id'), 'depreciacion_activos', ['public_id'], unique=True)
    op.create_index(op.f('ix_depreciacion_activos_updated_at'), 'depreciacion_activos', ['updated_at'], unique=False)
    op.create_index(op.f('ix_depreciacion_activos_updated_by'), 'depreciacion_activos', ['updated_by'], unique=False)

    # --- detalles_declaracion_impuesto (AuditableFull) ---
    op.create_table('detalles_declaracion_impuesto',
        sa.Column('declaracion_id', sa.BigInteger(), nullable=False),
        sa.Column('casilla_sat_id', sa.BigInteger(), nullable=False),
        sa.Column('base_imponible', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('monto_impuesto', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('es_ajuste_manual', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('motivo_ajuste', sa.Text(), nullable=True),
        sa.Column('ajustado_por', sa.BigInteger(), nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['declaracion_id'], ['declaraciones_impuesto.id'], name=op.f('fk_detalles_declaracion_impuesto_declaracion_id_declaraciones_impuesto'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['casilla_sat_id'], ['public.casillas_sat.id'], name=op.f('fk_detalles_declaracion_impuesto_casilla_sat_id_casillas_sat')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_detalles_declaracion_impuesto'))
    )
    op.create_index(op.f('ix_detalles_declaracion_impuesto_created_at'), 'detalles_declaracion_impuesto', ['created_at'], unique=False)
    op.create_index(op.f('ix_detalles_declaracion_impuesto_created_by'), 'detalles_declaracion_impuesto', ['created_by'], unique=False)
    op.create_index(op.f('ix_detalles_declaracion_impuesto_public_id'), 'detalles_declaracion_impuesto', ['public_id'], unique=True)
    op.create_index(op.f('ix_detalles_declaracion_impuesto_updated_at'), 'detalles_declaracion_impuesto', ['updated_at'], unique=False)
    op.create_index(op.f('ix_detalles_declaracion_impuesto_updated_by'), 'detalles_declaracion_impuesto', ['updated_by'], unique=False)

    # ============================================================
    # NIVEL 4: Última tabla (drill-down)
    # ============================================================
    
    # --- declaraciones_impuesto_facturas (AuditableFull) ---
    op.create_table('declaraciones_impuesto_facturas',
        sa.Column('detalle_declaracion_id', sa.BigInteger(), nullable=False),
        sa.Column('factura_id', sa.BigInteger(), nullable=False),
        sa.Column('base_asignada', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('impuesto_asignado', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        # BIGINT PK + public_id
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        # AuditableFull
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True, comment='Usuario que modificó el registro por última vez'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True, comment='Usuario que creó el registro'),
        sa.ForeignKeyConstraint(['detalle_declaracion_id'], ['detalles_declaracion_impuesto.id'], name=op.f('fk_declaraciones_impuesto_facturas_detalle_declaracion_id_detalles_declaracion_impuesto'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['factura_id'], ['facturas_electronicas.id'], name=op.f('fk_declaraciones_impuesto_facturas_factura_id_facturas_electronicas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_declaraciones_impuesto_facturas')),
        sa.UniqueConstraint('detalle_declaracion_id', 'factura_id', name='uq_detalle_factura')
    )
    op.create_index(op.f('ix_declaraciones_impuesto_facturas_created_at'), 'declaraciones_impuesto_facturas', ['created_at'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_facturas_created_by'), 'declaraciones_impuesto_facturas', ['created_by'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_facturas_public_id'), 'declaraciones_impuesto_facturas', ['public_id'], unique=True)
    op.create_index(op.f('ix_declaraciones_impuesto_facturas_updated_at'), 'declaraciones_impuesto_facturas', ['updated_at'], unique=False)
    op.create_index(op.f('ix_declaraciones_impuesto_facturas_updated_by'), 'declaraciones_impuesto_facturas', ['updated_by'], unique=False)

    # ============================================================
    # AGREGAR FKs DIFERIDAS
    # ============================================================
    
    # 1. FKs de empresas a plan_cuentas (dependencia circular resuelta)
    op.create_foreign_key(
        'fk_empresas_cuenta_utilidad_periodo_id_plan_cuentas',
        'empresas', 'plan_cuentas',
        ['cuenta_utilidad_periodo_id'], ['id']
    )
    op.create_foreign_key(
        'fk_empresas_cuenta_utilidades_acumuladas_id_plan_cuentas',
        'empresas', 'plan_cuentas',
        ['cuenta_utilidades_acumuladas_id'], ['id']
    )
    
    # 2. FKs de activos_fijos a plan_cuentas
    op.create_foreign_key(
        'fk_activos_fijos_cuenta_gasto_id_plan_cuentas',
        'activos_fijos', 'plan_cuentas',
        ['cuenta_gasto_id'], ['id']
    )
    op.create_foreign_key(
        'fk_activos_fijos_cuenta_depreciacion_acumulada_id_plan_cuentas',
        'activos_fijos', 'plan_cuentas',
        ['cuenta_depreciacion_acumulada_id'], ['id']
    )
    
    # 3. FKs de auditoría (created_by/updated_by → public.users.id)
    # TODAS las tablas del tenant tienen AuditableFull
    tablas_tenant_auditable_full = [
        'empresas', 'domicilios', 'representantes_legales', 'plan_cuentas',
        'periodos_fiscales', 'partidas', 'facturas_electronicas', 'sat_libros',
        'activos_fijos', 'declaraciones_impuesto', 'detalle_partidas',
        'factura_detalles', 'facturas_impuestos_especiales', 'sat_libros_lineas',
        'depreciacion_activos', 'detalles_declaracion_impuesto', 'declaraciones_impuesto_facturas'
    ]
    
    for tabla in tablas_tenant_auditable_full:
        # FK created_by → public.users.id
        op.create_foreign_key(
            f'fk_{tabla}_created_by_users',
            tabla, 'users',
            ['created_by'], ['id'],
            ondelete='SET NULL',
            referent_schema='public'
        )
        # FK updated_by → public.users.id
        op.create_foreign_key(
            f'fk_{tabla}_updated_by_users',
            tabla, 'users',
            ['updated_by'], ['id'],
            ondelete='SET NULL',
            referent_schema='public'
        )


def downgrade() -> None:
    """
    Elimina todas las tablas del schema del tenant en orden inverso.
    """
    
    # ============================================================
    # ELIMINAR FKs DIFERIDAS (en orden inverso)
    # ============================================================
    
    # 1. FKs de auditoría
    tablas_tenant_auditable_full = [
        'empresas', 'domicilios', 'representantes_legales', 'plan_cuentas',
        'periodos_fiscales', 'partidas', 'facturas_electronicas', 'sat_libros',
        'activos_fijos', 'declaraciones_impuesto', 'detalle_partidas',
        'factura_detalles', 'facturas_impuestos_especiales', 'sat_libros_lineas',
        'depreciacion_activos', 'detalles_declaracion_impuesto', 'declaraciones_impuesto_facturas'
    ]
    
    for tabla in tablas_tenant_auditable_full:
        op.drop_constraint(f'fk_{tabla}_updated_by_users', tabla, type_='foreignkey')
        op.drop_constraint(f'fk_{tabla}_created_by_users', tabla, type_='foreignkey')
    
    # 2. FKs de activos_fijos a plan_cuentas
    op.drop_constraint('fk_activos_fijos_cuenta_depreciacion_acumulada_id_plan_cuentas', 'activos_fijos', type_='foreignkey')
    op.drop_constraint('fk_activos_fijos_cuenta_gasto_id_plan_cuentas', 'activos_fijos', type_='foreignkey')
    
    # 3. FKs de empresas a plan_cuentas
    op.drop_constraint('fk_empresas_cuenta_utilidades_acumuladas_id_plan_cuentas', 'empresas', type_='foreignkey')
    op.drop_constraint('fk_empresas_cuenta_utilidad_periodo_id_plan_cuentas', 'empresas', type_='foreignkey')
    
    # ============================================================
    # ELIMINAR TABLAS (en orden inverso al upgrade)
    # ============================================================
    
    # Nivel 4
    op.drop_table('declaraciones_impuesto_facturas')
    
    # Nivel 3
    op.drop_table('detalles_declaracion_impuesto')
    op.drop_table('depreciacion_activos')
    op.drop_table('sat_libros_lineas')
    op.drop_table('facturas_impuestos_especiales')
    op.drop_table('factura_detalles')
    op.drop_table('detalle_partidas')
    
    # Nivel 2
    op.drop_table('declaraciones_impuesto')
    op.drop_table('activos_fijos')
    op.drop_table('sat_libros')
    op.drop_table('facturas_electronicas')
    op.drop_table('partidas')
    
    # Nivel 1
    op.drop_table('periodos_fiscales')
    op.drop_table('secuencias')
    op.drop_table('plan_cuentas')
    op.drop_table('representantes_legales')
    op.drop_table('domicilios')
    
    # Nivel 0
    op.drop_table('empresas')