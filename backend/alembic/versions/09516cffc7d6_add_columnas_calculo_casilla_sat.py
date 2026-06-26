"""add_columnas_calculo_casilla_sat

Revision ID: 09516cffc7d6
Revises: f9dcec18e03b
Create Date: 2026-06-25 10:12:15.005575

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '09516cffc7d6'
down_revision: Union[str, None] = 'f9dcec18e03b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna para dependencias de otras casillas (grafo de cálculo)
    op.add_column(
        'casillas_sat',
        sa.Column('dependencias', sa.JSON(), nullable=True, 
                  comment="Lista de códigos de casillas de las que depende")
    )
    
    # Agregar columna para función de cálculo especializada
    op.add_column(
        'casillas_sat',
        sa.Column('funcion_calculo', sa.String(50), nullable=True, 
                  comment="Nombre de función especializada (ej: isr_progresivo)")
    )
    
    # Agregar columna para parámetros de la función
    op.add_column(
        'casillas_sat',
        sa.Column('parametros_funcion', sa.JSON(), nullable=True, 
                  comment="Parámetros JSON para la función de cálculo")
    )


def downgrade() -> None:
    op.drop_column('casillas_sat', 'parametros_funcion')
    op.drop_column('casillas_sat', 'funcion_calculo')
    op.drop_column('casillas_sat', 'dependencias')
