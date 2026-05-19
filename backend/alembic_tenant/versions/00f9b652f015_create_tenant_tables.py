"""create_tenant_tables

Revision ID: 00f9b652f015
Revises: 0c22c15aa3d8
Create Date: 2026-05-17 11:27:16.039805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '00f9b652f015'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    op.create_table(
        'empresas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('nit', sa.String(20), unique=True, nullable=False),
        sa.Column('direccion', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=tenant_schema
    )
    op.create_table(
        'plan_cuentas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codigo', sa.String(20), unique=True, nullable=False),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('naturaleza', sa.String(10), nullable=False),
        sa.Column('acepta_tercero', sa.Boolean(), default=False),
        sa.Column('nivel', sa.Integer(), default=1),
        sa.Column('cuenta_padre_id', UUID(as_uuid=True), nullable=True),
        sa.Column('activa', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=tenant_schema
    )

def downgrade():
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_table('plan_cuentas', schema=tenant_schema)
    op.drop_table('empresas', schema=tenant_schema)