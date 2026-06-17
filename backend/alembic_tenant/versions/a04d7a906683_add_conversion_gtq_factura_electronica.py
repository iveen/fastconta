"""add_conversion_gtq_factura_electronica

Revision ID: a04d7a906683
Revises: 40d37ae3e47b
Create Date: 2026-06-16 09:13:18.490048

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a04d7a906683'
down_revision: Union[str, None] = '40d37ae3e47b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # Agregar columnas para montos en GTQ
    op.add_column('facturas_electronicas', sa.Column('total_gravado_gtq', sa.Numeric(15, 2), nullable=False, server_default='0'))
    op.add_column('facturas_electronicas', sa.Column('total_iva_gtq', sa.Numeric(15, 2), nullable=False, server_default='0'))
    op.add_column('facturas_electronicas', sa.Column('total_exento_gtq', sa.Numeric(15, 2), server_default='0'))
    op.add_column('facturas_electronicas', sa.Column('total_gtq', sa.Numeric(15, 2), nullable=False, server_default='0'))

    # Agregar columnas para montos en GTQ en detalles
    op.add_column('factura_detalles', sa.Column('precio_unitario_gtq', sa.Numeric(12, 2), nullable=False, server_default='0'))
    op.add_column('factura_detalles', sa.Column('total_linea_gtq', sa.Numeric(12, 2), nullable=False, server_default='0'))
    op.add_column('factura_detalles', sa.Column('iva_linea_gtq', sa.Numeric(12, 2), server_default='0'))
           
    # 🔹 CRÍTICO: Calcular valores para facturas existentes
    # Multiplicar montos originales por tipo_cambio
    op.execute("""
        UPDATE facturas_electronicas
        SET 
            total_gravado_gtq = total_gravado * tipo_cambio,
            total_iva_gtq = total_iva * tipo_cambio,
            total_exento_gtq = total_exento * tipo_cambio,
            total_gtq = total * tipo_cambio
    """)

    # 🔹 CRÍTICO: Calcular valores para detalles existentes
    # Necesitamos hacer un JOIN con facturas_electronicas para obtener el tipo_cambio
    op.execute("""
        UPDATE factura_detalles fd
        SET 
            precio_unitario_gtq = fd.precio_unitario * fe.tipo_cambio,
            total_linea_gtq = fd.total_linea * fe.tipo_cambio,
            iva_linea_gtq = fd.iva_linea * fe.tipo_cambio
        FROM facturas_electronicas fe
        WHERE fd.factura_id = fe.id
    """)


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    op.drop_column('facturas_electronicas', 'total_gtq')
    op.drop_column('facturas_electronicas', 'total_exento_gtq')
    op.drop_column('facturas_electronicas', 'total_iva_gtq')
    op.drop_column('facturas_electronicas', 'total_gravado_gtq')

    op.drop_column('factura_detalles', 'iva_linea_gtq')
    op.drop_column('factura_detalles', 'total_linea_gtq')
    op.drop_column('factura_detalles', 'precio_unitario_gtq')
