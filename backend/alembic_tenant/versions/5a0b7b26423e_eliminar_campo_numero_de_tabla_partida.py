"""eliminar campo numero de tabla Partida

Revision ID: 5a0b7b26423e
Revises: 7660b41a3d2
Create Date: 2026-06-08 18:28:08.139286

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5a0b7b26423e'
down_revision: Union[str, None] = '7660b41a3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # 1. Eliminar la columna 'numero' de la tabla 'partidas'
    # PostgreSQL eliminará automáticamente la secuencia si es propiedad de esta columna
    op.drop_column('partidas', 'numero')
    
    # 2. Por seguridad, eliminamos la secuencia explícitamente si aún existiera
    op.execute("DROP SEQUENCE IF EXISTS partidas_numero_seq")
    


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # 1. Recrear la secuencia
    op.execute("CREATE SEQUENCE IF NOT EXISTS partidas_numero_seq")
    
    # 2. Agregar la columna 'numero' de nuevo
    op.add_column(
        'partidas', 
        sa.Column(
            'numero', 
            sa.Integer(), 
            sa.Sequence('partidas_numero_seq'), 
            unique=True, 
            nullable=False,
            server_default=sa.text("nextval('partidas_numero_seq')")
        )
    )
    
    # 3. Recrear la restricción de unicidad (por si acaso no se aplicó con el add_column)
    op.create_unique_constraint('uq_partidas_numero', 'partidas', ['numero'])

