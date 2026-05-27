"""add: catalogo impuestos especiales

Revision ID: 3430da52ddb9
Revises: 873a7d9ea9d4
Create Date: 2026-05-26 11:58:07.544183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3430da52ddb9'
down_revision: Union[str, None] = '873a7d9ea9d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'catalogo_impuestos_especiales',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codigo', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        schema='public'
    )

def downgrade():
    op.drop_table('catalogo_impuestos_especiales', schema='public')
