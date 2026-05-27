"""add: campos para validación de facturas electrónicas

Revision ID: ba7325eae3fc
Revises: ebd343641e3c
Create Date: 2026-05-26 17:51:28.329520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba7325eae3fc'
down_revision: Union[str, None] = 'ebd343641e3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ Idempotentes: no fallan si la columna ya existe
    op.execute("ALTER TABLE facturas_electronicas ADD COLUMN IF NOT EXISTS xml_filename VARCHAR(255)")
    op.execute("ALTER TABLE facturas_electronicas ADD COLUMN IF NOT EXISTS validado BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE facturas_electronicas ADD COLUMN IF NOT EXISTS fecha_validacion TIMESTAMP WITH TIME ZONE")

def downgrade() -> None:
    op.execute("ALTER TABLE facturas_electronicas DROP COLUMN IF EXISTS fecha_validacion")
    op.execute("ALTER TABLE facturas_electronicas DROP COLUMN IF EXISTS validado")
    op.execute("ALTER TABLE facturas_electronicas DROP COLUMN IF EXISTS xml_filename")
