"""add_requiere_revision_factura_ocr

Revision ID: 73831a4c2c00
Revises: 36c4b2fdaa6d
Create Date: 2026-07-06 11:20:03.209656

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '73831a4c2c00'
down_revision: Union[str, None] = '36c4b2fdaa6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Skip para el tenant 'system' (esquema vacío para superadmin)
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.add_column('facturas_electronicas', sa.Column('requiere_revision_manual', sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    # Skip para el tenant 'system' (esquema vacío para superadmin)
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_column('facturas_electronicas', 'requiere_revision_manual')
