"""add_modelos_activos_fijos

Revision ID: 773aab3dc84c
Revises: fa5c063af104
Create Date: 2026-06-03 12:36:19.239825
"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '773aab3dc84c'
down_revision: Union[str, None] = 'fa5c063af104'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Proteger el esquema 'system' (superadmin) de recibir tablas de datos de tenant
    schema_actual = os.environ.get("TENANT_SCHEMA", "public")
    if schema_actual == 'system':
        return

    # =========================================================================
    # 1. Tabla: activos_fijos
    # =========================================================================
    op.create_table(
        'activos_fijos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('empresa_id', UUID(as_uuid=True), nullable=False),
        sa.Column('categoria_id', UUID(as_uuid=True), nullable=False),
        sa.Column('codigo_interno', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=False),
        sa.Column('fecha_adquisicion', sa.Date(), nullable=False),
        sa.Column('valor_costo', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('valor_residual', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('tasa_depreciacion_anual_aplicada', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('vida_util_meses_aplicada', sa.Integer(), nullable=False),
        sa.Column('cuenta_gasto_id', UUID(as_uuid=True), nullable=True),
        sa.Column('cuenta_depreciacion_acumulada_id', UUID(as_uuid=True), nullable=True),
        sa.Column('estado', sa.String(length=30), nullable=False, server_default='activo'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        
        # Foreign Keys (Nota el uso de f'{schema_actual}.' para tablas del tenant)
        sa.ForeignKeyConstraint(['categoria_id'], ['public.categorias_activos_fijos.id'], ),
        sa.ForeignKeyConstraint(['cuenta_depreciacion_acumulada_id'], [f'{schema_actual}.plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['cuenta_gasto_id'], [f'{schema_actual}.plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], [f'{schema_actual}.empresas.id'], ),
        
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('tasa_depreciacion_anual_aplicada >= 0 AND tasa_depreciacion_anual_aplicada <= 100', name='chk_activos_fijos_tasa_valida'),
        schema=schema_actual
    )

    # Índices para optimizar consultas por empresa
    op.create_index('ix_activos_fijos_empresa_id', 'activos_fijos', ['empresa_id'], schema=schema_actual)


    # =========================================================================
    # 2. Tabla: depreciacion_activos
    # =========================================================================
    op.create_table(
        'depreciacion_activos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('empresa_id', UUID(as_uuid=True), nullable=False),
        sa.Column('activo_id', UUID(as_uuid=True), nullable=False),
        sa.Column('anio_periodo', sa.SmallInteger(), nullable=False),
        sa.Column('mes_periodo', sa.SmallInteger(), nullable=False),
        sa.Column('monto_depreciacion_mes', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('depreciacion_acumulada_hasta_fecha', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('valor_en_libros', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('partida_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        
        # Foreign Keys (Usando schema_actual dinámico)
        sa.ForeignKeyConstraint(['activo_id'], [f'{schema_actual}.activos_fijos.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], [f'{schema_actual}.empresas.id'], ),
        sa.ForeignKeyConstraint(['partida_id'], [f'{schema_actual}.partidas.id'], ),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('activo_id', 'anio_periodo', 'mes_periodo', name='uq_depreciacion_activo_periodo'),
        sa.CheckConstraint('mes_periodo BETWEEN 1 AND 12', name='chk_depreciacion_mes_valido'),
        schema=schema_actual
    )

    # Índice compuesto para consultas rápidas de cierre mensual por empresa
    op.create_index(
        'idx_depreciacion_activos_empresa_periodo', 
        'depreciacion_activos', 
        ['empresa_id', 'anio_periodo', 'mes_periodo'], 
        schema=schema_actual
    )


def downgrade() -> None:
    # Proteger el esquema 'system' en el rollback
    schema_actual = os.environ.get("TENANT_SCHEMA", "public")
    if schema_actual == 'system':
        return

    # Eliminar en orden inverso al de creación para evitar errores de dependencias de FK
    op.drop_index('idx_depreciacion_activos_empresa_periodo', table_name='depreciacion_activos', schema=schema_actual)
    op.drop_table('depreciacion_activos', schema=schema_actual)

    op.drop_index('ix_activos_fijos_empresa_id', table_name='activos_fijos', schema=schema_actual)
    op.drop_table('activos_fijos', schema=schema_actual)