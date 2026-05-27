"""add xml_filename to facturas_electronicas

Revision ID: ebd343641e3c
Revises: e7441e6b3151
Create Date: 2026-05-26 16:59:47.503696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebd343641e3c'
down_revision: Union[str, None] = 'e7441e6b3151'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Agregar columna (idempotente)
    op.execute("""
        ALTER TABLE facturas_electronicas 
        ADD COLUMN IF NOT EXISTS xml_filename VARCHAR(255)
    """)
    # Índice para búsquedas rápidas en validación
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_facturas_xml_filename 
        ON facturas_electronicas (xml_filename)
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_facturas_xml_filename")
    op.execute("ALTER TABLE facturas_electronicas DROP COLUMN IF EXISTS xml_filename")
