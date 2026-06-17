"""add_declaraciones_impuesto_tenant

Revision ID: 617b762b3b44
Revises: 75ecd82b4a06
Create Date: 2026-06-11 10:25:49.982050

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '617b762b3b44'
down_revision: Union[str, None] = '75ecd82b4a06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # =========================================================================
    # 1. Cabecera de la Declaración Sombra (Tenant)
    # =========================================================================
    op.create_table(
        'declaraciones_impuesto',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # FK al tenant (sin prefijo, asume el esquema actual del tenant)
        sa.Column('empresa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=False, index=True),
        # FK al catálogo global (CON prefijo 'public.' explícito)
        sa.Column('formulario_sat_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public.formularios_sat.id'), nullable=False),
        
        sa.Column('anio', sa.SmallInteger, nullable=False, index=True),
        sa.Column('mes', sa.SmallInteger, nullable=False, index=True),
        sa.Column('estado', sa.String(20), nullable=False, server_default='BORRADOR'),
        
        # Totales Financieros
        sa.Column('total_debito_fiscal', sa.Numeric(15, 2), server_default='0'),
        sa.Column('total_credito_fiscal', sa.Numeric(15, 2), server_default='0'),
        sa.Column('impuesto_determinado', sa.Numeric(15, 2), server_default='0'),
        sa.Column('remanente_periodo_anterior', sa.Numeric(15, 2), server_default='0'),
        sa.Column('remanente_siguiente_periodo', sa.Numeric(15, 2), server_default='0'),
        sa.Column('impuesto_a_pagar', sa.Numeric(15, 2), server_default='0'),
        
        # Auditoría
        sa.Column('finalizado_por', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('fecha_cierre', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        sa.UniqueConstraint('empresa_id', 'formulario_sat_id', 'anio', 'mes', name='uq_declaracion_periodo')
    )

    # =========================================================================
    # 2. Detalle (Casillas del formulario)
    # =========================================================================
    op.create_table(
        'detalles_declaracion_impuesto',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('declaracion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('declaraciones_impuesto.id', ondelete='CASCADE'), nullable=False),
        # FK al catálogo global (CON prefijo 'public.' explícito)
        sa.Column('casilla_sat_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public.casillas_sat.id'), nullable=False),
        
        sa.Column('base_imponible', sa.Numeric(15, 2), server_default='0'),
        sa.Column('monto_impuesto', sa.Numeric(15, 2), server_default='0'),
        
        sa.Column('es_ajuste_manual', sa.Boolean, server_default='false'),
        sa.Column('motivo_ajuste', sa.Text, nullable=True),
        sa.Column('ajustado_por', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Índice para acelerar la búsqueda de detalles por declaración
    op.create_index('idx_detalles_declaracion_id', 'detalles_declaracion_impuesto', ['declaracion_id'])

    # =========================================================================
    # 3. Trazabilidad (Drill-down a facturas)
    # =========================================================================
    op.create_table(
        'declaraciones_impuesto_facturas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('detalle_declaracion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('detalles_declaracion_impuesto.id', ondelete='CASCADE'), nullable=False),
        # FK al tenant (sin prefijo)
        sa.Column('factura_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facturas_electronicas.id'), nullable=False),
        
        sa.Column('base_asignada', sa.Numeric(15, 2), server_default='0'),
        sa.Column('impuesto_asignado', sa.Numeric(15, 2), server_default='0'),
        
        sa.UniqueConstraint('detalle_declaracion_id', 'factura_id', name='uq_detalle_factura')
    )

def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # El orden de eliminación es CRÍTICO: primero las tablas hijas, luego las padres.
    op.drop_table('declaraciones_impuesto_facturas')
    op.drop_index('idx_detalles_declaracion_id', table_name='detalles_declaracion_impuesto')
    op.drop_table('detalles_declaracion_impuesto')
    op.drop_table('declaraciones_impuesto')
