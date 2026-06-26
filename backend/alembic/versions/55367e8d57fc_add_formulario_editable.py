"""add_formulario_editable

Revision ID: 55367e8d57fc
Revises: 342af5a7af9b
Create Date: 2026-06-23 09:53:19.508956

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '55367e8d57fc'
down_revision: Union[str, None] = '342af5a7af9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna 'editable' con valor por defecto True
    op.add_column(
        'formularios_sat',
        sa.Column('editable', sa.Boolean(), nullable=False, server_default=sa.text('true'), default=True)
    )


def downgrade() -> None:
    # Eliminar columna 'editable'
    op.drop_column('formularios_sat', 'editable')
