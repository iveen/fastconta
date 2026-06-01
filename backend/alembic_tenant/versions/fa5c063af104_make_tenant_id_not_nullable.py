"""make tenant_id not nullable

Revision ID: fa5c063af104
Revises: eb56e970ccc9
Create Date: 2026-05-31 21:10:18.353795

"""
import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fa5c063af104'
down_revision: Union[str, None] = 'eb56e970ccc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.alter_column('empresas', 'tenant_id', nullable=False)

def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_index('ix_empresas_tenant_id', table_name='empresas')
    op.drop_column('empresas', 'tenant_id')
