"""add_factura_detalles

Revision ID: 85e51fb13be5
Revises: a4f888d8ea41
Create Date: 2026-05-21 17:45:50.118624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = '85e51fb13be5'
down_revision: Union[str, None] = 'a4f888d8ea41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.create_table(
        'factura_detalles',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('factura_id', sa.UUID(as_uuid=True), sa.ForeignKey('facturas_electronicas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cantidad', sa.Numeric(12,4), nullable=False),
        sa.Column('descripcion', sa.String(500), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(12,2), nullable=False),
        sa.Column('total_linea', sa.Numeric(12,2), nullable=False),
        sa.Column('iva_linea', sa.Numeric(12,2), server_default='0'),
        schema=tenant_schema
    )

def downgrade():    
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_table('factura_detalles', schema=tenant_schema)
