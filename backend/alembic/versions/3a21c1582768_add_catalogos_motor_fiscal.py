"""add_catalogos_motor_fiscal

Revision ID: 3a21c1582768
Revises: d959b3bdf565
Create Date: 2026-06-05 13:22:47.376951

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '3a21c1582768'
down_revision: Union[str, None] = 'd959b3bdf565'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # 1. CATEGORIAS DE ACTIVOS FIJOS (Agregar descripcion)
    # =========================================================================
    op.add_column(
        'categorias_activos_fijos', 
        sa.Column('descripcion', sa.Text(), nullable=True), 
        schema='public'
    )

    # =========================================================================
    # 2. CATALOGO DE IMPUESTOS (CREAR PRIMERO - Tabla Base)
    # =========================================================================
    op.create_table(
        'catalogo_impuestos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('codigo', sa.String(length=20), nullable=False, index=True),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion_legal', sa.Text(), nullable=False),
        sa.Column('tasa_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('tasa_fija_monto', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_inferior', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_superior', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('frecuencia_pago', sa.String(length=20), nullable=False),
        sa.Column('frecuencia_liquidacion', sa.String(length=20), nullable=False),
        sa.Column('es_acreditable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requiere_autorizacion_sat', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
        schema='public'
    )

    # =========================================================================
    # 3. REGIMENES FISCALES (Agregar codigo y descripcion)
    # =========================================================================
    op.add_column(
        'regimenes_fiscales', 
        sa.Column('codigo', sa.String(length=50), nullable=True), 
        schema='public'
    )
    op.add_column(
        'regimenes_fiscales', 
        sa.Column('descripcion', sa.Text(), nullable=True), 
        schema='public'
    )
    
    # Mapeo explícito de códigos para regímenes existentes
    mapeo_codigos = {
        "Pequeño Contribuyente Electrónico - 4%": "PC_FEL",
        "Pequeño Contribuyente Electrónico (FEL)": "PC_FEL",
        "Pequeño Contribuyente Manual - 5%": "PC_MANUAL",
        "Pequeño Contribuyente Manual": "PC_MANUAL",
        "Opcional Simplificado": "ROS",
        "Regimen Opcional Simplificado": "ROS",
        "Sobre Utilidades": "RG_UTILIDADES",
        "Regimen General Sobre Utilidades": "RG_UTILIDADES",
        "Regimen Sobre Utilidades": "RG_UTILIDADES",
        "Rentas del Trabajo": "RENTA_TRABAJO",
        "Rentas del Trabajo (Asalariados)": "RENTA_TRABAJO",
        "Especial Agropecuario": "AGROPECUARIO",
        "Régimen de Exportación": "EXPORTACION",
        "Regimen de Exportacion": "EXPORTACION",
        "Retención a No Residentes": "NO_RESIDENTES",
        "Retencion a No Residentes": "NO_RESIDENTES",
        "Específico": "ESPECIFICO",
        "Especifico": "ESPECIFICO"
    }
    
    for nombre_regimen, codigo_regimen in mapeo_codigos.items():
        op.execute(f"""
            UPDATE public.regimenes_fiscales 
            SET codigo = '{codigo_regimen}' 
            WHERE nombre = '{nombre_regimen}' AND codigo IS NULL
        """)
    
    op.execute("""
        UPDATE public.regimenes_fiscales 
        SET codigo = 'REGIMEN_' || LEFT(REPLACE(id::text, '-', ''), 8)
        WHERE codigo IS NULL
    """)
    
    op.alter_column('regimenes_fiscales', 'codigo', nullable=False, schema='public')
    op.create_unique_constraint('uq_regimenes_fiscales_codigo', 'regimenes_fiscales', ['codigo'], schema='public')
    op.create_index('ix_regimenes_fiscales_codigo', 'regimenes_fiscales', ['codigo'], schema='public')

    # =========================================================================
    # 4. TABLA PUENTE: REGIMEN IMPUESTO CONFIG (AHORA SÍ PUEDE CREARSE)
    # =========================================================================
    op.create_table(
        'regimen_impuesto_config',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('regimen_id', UUID(as_uuid=True), nullable=False),
        sa.Column('impuesto_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tasa_porcentaje', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('tasa_fija_monto', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_inferior', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=True),
        sa.Column('limite_superior', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('es_acreditable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('es_retencion_definitiva', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requiere_autorizacion_sat', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['impuesto_id'], ['public.catalogo_impuestos.id'], ),
        sa.ForeignKeyConstraint(['regimen_id'], ['public.regimenes_fiscales.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('regimen_id', 'impuesto_id', name='uq_regimen_impuesto_unico'),
        schema='public'
    )
    
    op.create_index('ix_regimen_impuesto_config_regimen_id', 'regimen_impuesto_config', ['regimen_id'], schema='public')
    op.create_index('ix_regimen_impuesto_config_impuesto_id', 'regimen_impuesto_config', ['impuesto_id'], schema='public')


def downgrade() -> None:
    op.drop_index('ix_regimen_impuesto_config_impuesto_id', table_name='regimen_impuesto_config', schema='public')
    op.drop_index('ix_regimen_impuesto_config_regimen_id', table_name='regimen_impuesto_config', schema='public')
    op.drop_table('regimen_impuesto_config', schema='public')

    op.drop_index('ix_regimenes_fiscales_codigo', table_name='regimenes_fiscales', schema='public')
    op.drop_constraint('uq_regimenes_fiscales_codigo', 'regimenes_fiscales', schema='public', type_='unique')
    op.drop_column('regimenes_fiscales', 'descripcion', schema='public')
    op.drop_column('regimenes_fiscales', 'codigo', schema='public')

    op.drop_table('catalogo_impuestos', schema='public')

    op.drop_column('categorias_activos_fijos', 'descripcion', schema='public')