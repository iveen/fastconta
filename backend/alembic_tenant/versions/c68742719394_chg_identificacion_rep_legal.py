"""chg_identificacion_rep_legal

Revision ID: c68742719394
Revises: 01ace1ffe273
Create Date: 2026-07-02 07:31:19.555029

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c68742719394'
down_revision: Union[str, None] = '01ace1ffe273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.add_column('representantes_legales', sa.Column('tipo_identificacion', sa.String(length=20), nullable=False))
    op.add_column('representantes_legales', sa.Column('numero_identificacion', sa.String(length=20), nullable=False))
    op.drop_column('representantes_legales', 'dpi')  


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.add_column('representantes_legales', sa.Column('dpi', sa.String(length=20), nullable=False))
    op.drop_column('representantes_legales', 'tipo_identificacion')
    op.drop_column('representantes_legales', 'numero_identificacion')
