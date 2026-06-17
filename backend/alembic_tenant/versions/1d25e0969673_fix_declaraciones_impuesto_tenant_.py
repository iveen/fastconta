"""fix_declaraciones_impuesto_tenant_schemas

Revision ID: 1d25e0969673
Revises: 617b762b3b44
Create Date: 2026-06-12 10:52:52.939680

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1d25e0969673'
down_revision: Union[str, None] = '617b762b3b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # 1. Obtener todos los esquemas de tenants existentes (excluyendo 'system' o 'public' si no es un tenant real)
    result = conn.execute(sa.text("SELECT schema_name FROM public.tenants WHERE schema_name NOT IN ('system', 'public')"))
    tenant_schemas = [row[0] for row in result.fetchall()]
    
    if not tenant_schemas:
        return
    
    for schema in tenant_schemas:
        # Crear declaraciones_impuesto en el esquema específico del tenant
        op.create_table(
            'declaraciones_impuesto',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('empresa_id', postgresql.UUID(as_uuid=True), sa.ForeignKey(f'{schema}.empresas.id'), nullable=False, index=True),
            sa.Column('formulario_sat_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public.formularios_sat.id'), nullable=False),
            sa.Column('anio', sa.SmallInteger, nullable=False, index=True),
            sa.Column('mes', sa.SmallInteger, nullable=False, index=True),
            sa.Column('estado', sa.String(20), nullable=False, server_default='BORRADOR'),
            sa.Column('total_debito_fiscal', sa.Numeric(15, 2), server_default='0'),
            sa.Column('total_credito_fiscal', sa.Numeric(15, 2), server_default='0'),
            sa.Column('impuesto_determinado', sa.Numeric(15, 2), server_default='0'),
            sa.Column('remanente_periodo_anterior', sa.Numeric(15, 2), server_default='0'),
            sa.Column('remanente_siguiente_periodo', sa.Numeric(15, 2), server_default='0'),
            sa.Column('impuesto_a_pagar', sa.Numeric(15, 2), server_default='0'),
            sa.Column('finalizado_por', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('fecha_cierre', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint('empresa_id', 'formulario_sat_id', 'anio', 'mes', name=f'uq_declaracion_periodo_{schema}'),
            schema=schema  # <--- CLAVE: Crea la tabla en este esquema específico
        )

        # Crear detalles_declaracion_impuesto
        op.create_table(
            'detalles_declaracion_impuesto',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('declaracion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey(f'{schema}.declaraciones_impuesto.id', ondelete='CASCADE'), nullable=False),
            sa.Column('casilla_sat_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public.casillas_sat.id'), nullable=False),
            sa.Column('base_imponible', sa.Numeric(15, 2), server_default='0'),
            sa.Column('monto_impuesto', sa.Numeric(15, 2), server_default='0'),
            sa.Column('es_ajuste_manual', sa.Boolean, server_default='false'),
            sa.Column('motivo_ajuste', sa.Text, nullable=True),
            sa.Column('ajustado_por', postgresql.UUID(as_uuid=True), nullable=True),
            schema=schema  # <--- CLAVE
        )
        
        op.create_index('idx_detalles_declaracion_id', 'detalles_declaracion_impuesto', ['declaracion_id'], schema=schema)

        # Crear declaraciones_impuesto_facturas
        op.create_table(
            'declaraciones_impuesto_facturas',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('detalle_declaracion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey(f'{schema}.detalles_declaracion_impuesto.id', ondelete='CASCADE'), nullable=False),
            sa.Column('factura_id', postgresql.UUID(as_uuid=True), sa.ForeignKey(f'{schema}.facturas_electronicas.id'), nullable=False),
            sa.Column('base_asignada', sa.Numeric(15, 2), server_default='0'),
            sa.Column('impuesto_asignado', sa.Numeric(15, 2), server_default='0'),
            sa.UniqueConstraint('detalle_declaracion_id', 'factura_id', name=f'uq_detalle_factura_{schema}'),
            schema=schema  # <--- CLAVE
        )


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT schema_name FROM public.tenants WHERE schema_name NOT IN ('system', 'public')"))
    tenant_schemas = [row[0] for row in result.fetchall()]
    
    if not tenant_schemas:
        return
        
    for schema in tenant_schemas:
        op.drop_table('declaraciones_impuesto_facturas', schema=schema)
        op.drop_index('idx_detalles_declaracion_id', table_name='detalles_declaracion_impuesto', schema=schema)
        op.drop_table('detalles_declaracion_impuesto', schema=schema)
        op.drop_table('declaraciones_impuesto', schema=schema)
