"""create_facturas_electronicas

Revision ID: a4f888d8ea41
Revises: d90dd406e3ad
Create Date: 2026-05-21 15:18:03.223981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'a4f888d8ea41'
down_revision: Union[str, None] = 'd90dd406e3ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    op.create_table(
        'facturas_electronicas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('empresa_id', UUID(as_uuid=True), sa.ForeignKey('empresas.id'), nullable=False),
        sa.Column('xml_original', sa.Text(), nullable=False),
        sa.Column('numero_autorizacion', sa.String(50), nullable=False),
        sa.Column('serie', sa.String(20), nullable=True),
        sa.Column('numero', sa.String(20), nullable=False),
        sa.Column('fecha_emision', sa.DateTime(timezone=True), nullable=False),
        sa.Column('emisor_nit', sa.String(15), nullable=False),
        sa.Column('emisor_nombre', sa.String(255), nullable=False),
        sa.Column('receptor_nit', sa.String(15), nullable=False),
        sa.Column('receptor_nombre', sa.String(255), nullable=False),
        sa.Column('total_gravado', sa.Numeric(12,2), server_default='0'),
        sa.Column('total_iva', sa.Numeric(12,2), server_default='0'),
        sa.Column('total_exento', sa.Numeric(12,2), server_default='0'),
        sa.Column('total', sa.Numeric(12,2), nullable=False),
        sa.Column('autorizacion_uuid', sa.String(50), nullable=True),
        sa.Column('tipo_documento', sa.String(10), nullable=True),
        sa.Column('moneda', sa.String(5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=tenant_schema
    )

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_table('facturas_electronicas', schema=tenant_schema)