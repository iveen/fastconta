"""add_partidas

Revision ID: 90dab873f830
Revises: 00f9b652f015
Create Date: 2026-05-17 13:28:33.743076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '90dab873f830'
down_revision: Union[str, None] = '00f9b652f015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    op.create_table(
        'partidas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=tenant_schema
    )
    op.create_table(
        'detalle_partidas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('partida_id', UUID(as_uuid=True), nullable=False),
        sa.Column('cuenta_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tipo_movimiento', sa.String(10), nullable=False),
        sa.Column('monto', sa.Numeric(12,2), nullable=False),
        schema=tenant_schema
    )
    op.create_foreign_key('fk_detalle_partidas_partida', 'detalle_partidas', 'partidas',
                          ['partida_id'], ['id'], ondelete='CASCADE',
                          source_schema=tenant_schema, referent_schema=tenant_schema)
    op.create_foreign_key('fk_detalle_partidas_cuenta', 'detalle_partidas', 'plan_cuentas',
                          ['cuenta_id'], ['id'],
                          source_schema=tenant_schema, referent_schema=tenant_schema)

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_table('detalle_partidas', schema=tenant_schema)
    op.drop_table('partidas', schema=tenant_schema)