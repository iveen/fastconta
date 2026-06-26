"""del_columna_seccion_casillas

Revision ID: 3d672b42eb14
Revises: 09516cffc7d6
Create Date: 2026-06-25 10:46:11.921831

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3d672b42eb14'
down_revision: Union[str, None] = '09516cffc7d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar columna 'seccion' (se calcula vía property desde seccion_rel)
    op.drop_column('casillas_sat', 'seccion')


def downgrade() -> None:
    # Restaurar columna si es necesario
    op.add_column(
        'casillas_sat',
        sa.Column('seccion', sa.String(10), nullable=True)
    )
