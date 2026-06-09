"""add_tipo_origen_partida

Revision ID: d879be7df70d
Revises: 05301d15232a
Create Date: 2026-06-09 16:42:45.437059

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd879be7df70d'
down_revision: Union[str, None] = '05301d15232a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.add_column(
        'partidas',
        sa.Column(
            'tipo_origen',
            sa.String(50),
            nullable=False,
            server_default='manual'
        )
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    op.drop_column('partidas', 'tipo_origen')
