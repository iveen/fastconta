"""add tipo_cambio to facturas_electronicas

Revision ID: bdac449affae
Revises: 85e51fb13be5
Create Date: 2026-05-25 10:34:02.769364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = 'bdac449affae'
down_revision: Union[str, None] = '85e51fb13be5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.add_column(
        'facturas_electronicas', 
        sa.Column('tipo_cambio', sa.Numeric(10, 5), nullable=True)
    )

def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_column('facturas_electronicas', 'tipo_cambio')
