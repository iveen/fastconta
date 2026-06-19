"""drop_legacy_codigo_index

Revision ID: cdf4931118a9
Revises: e18def92e692
Create Date: 2026-06-18 20:34:28.234171

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cdf4931118a9'
down_revision: Union[str, None] = 'e18def92e692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # Dropear índice único legado sobre 'codigo' en casillas_sat
    # Este índice impedía que múltiples versiones del formulario tuvieran
    # casillas con el mismo código (ej: '3.1' en v1.0 y '3.1' en v2.0)
    # =========================================================================
    try:
        op.drop_index(
            'ix_public_casillas_sat_codigo',
            table_name='casillas_sat',
            schema='public'
        )
        print("✅ Dropeado índice único legado: ix_public_casillas_sat_codigo")
    except Exception as e:
        print(f"⚠️  No se pudo dropear ix_public_casillas_sat_codigo: {e}")
        # Intentar como constraint por si acaso
        try:
            op.drop_constraint(
                'ix_public_casillas_sat_codigo',
                'casillas_sat',
                schema='public',
                type_='unique'
            )
            print("✅ Dropeado constraint único legado: ix_public_casillas_sat_codigo")
        except Exception as e2:
            print(f"❌ Error dropeando constraint: {e2}")


def downgrade() -> None:
    # Recrear el índice único (no recomendado, pero por completitud)
    op.create_index(
        'ix_public_casillas_sat_codigo',
        'casillas_sat',
        ['codigo'],
        schema='public',
        unique=True
    )
