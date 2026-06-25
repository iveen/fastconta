"""add_seccion_casilla_automatica

Revision ID: f9dcec18e03b
Revises: 55367e8d57fc
Create Date: 2026-06-24 10:53:32.071722

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f9dcec18e03b'
down_revision: Union[str, None] = '55367e8d57fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna 'es_automatica' con valor por defecto True
    op.add_column(
        'casillas_sat',
        sa.Column('es_automatica', sa.Boolean(), nullable=False, server_default=sa.text('false'), default=False)
    )

    op.add_column(
        'secciones_formulario',
        sa.Column('es_automatica', sa.Boolean(), nullable=False, server_default=sa.text('false'), default=False)
    )


def downgrade() -> None:
    # Eliminar columna 'es_automatica'
    op.drop_column('casillas_sat', 'es_automatica')
    op.drop_column('secciones_formulario', 'es_automatica')
