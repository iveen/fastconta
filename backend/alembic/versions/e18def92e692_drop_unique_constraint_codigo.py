"""drop_unique_constraint_codigo

Revision ID: e18def92e692
Revises: 49129fce985b
Create Date: 2026-06-18 20:23:25.364313

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e18def92e692'
down_revision: Union[str, None] = '49129fce985b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dropear el índice único sobre 'codigo' que impide múltiples versiones
    try:
        op.drop_index('ix_public_formularios_sat_codigo', table_name='formularios_sat', schema='public')
        print("✅ Dropeado índice único: ix_public_formularios_sat_codigo")
    except Exception as e:
        print(f"⚠️  No se pudo dropear ix_public_formularios_sat_codigo: {e}")
        # Intentar con el nombre alternativo
        try:
            op.drop_constraint('ix_public_formularios_sat_codigo', 'formularios_sat', schema='public', type_='unique')
            print("✅ Dropeado constraint único: ix_public_formularios_sat_codigo")
        except Exception as e2:
            print(f"❌ Error dropeando constraint: {e2}")


def downgrade() -> None:
    # Recrear el índice único (no recomendado, pero por completitud)
    op.create_index(
        'ix_public_formularios_sat_codigo',
        'formularios_sat',
        ['codigo'],
        schema='public',
        unique=True
    )
