"""chg: cambio regimen normal por regimen general

Revision ID: 9122ea0c8c51
Revises: 21055b1fcffc
Create Date: 2026-05-27 11:15:45.480128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = '9122ea0c8c51'
down_revision: Union[str, None] = '21055b1fcffc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # 1. Limpiamos cualquier dato viejo: Si había registros como 'NORMAL', los migramos a 'GENERAL'
    op.execute("UPDATE sat_libros SET regimen_fiscal = 'GENERAL' WHERE regimen_fiscal = 'NORMAL'")

    # 2. Borrado quirúrgico y blindado usando SQL Nativo de Postgres.
    # Intentamos borrar ambos nombres posibles. Si no existen, Postgres simplemente los ignora gracias al 'IF EXISTS'
    op.execute('ALTER TABLE sat_libros DROP CONSTRAINT IF EXISTS "regimenfiscal";')
    op.execute('ALTER TABLE sat_libros DROP CONSTRAINT IF EXISTS "sat_libros_regimen_fiscal_check";')

    # 3. Creamos el nuevo constraint limpio y estandarizado con los valores correctos de la SAT
    with op.batch_alter_table('sat_libros', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'regimenfiscal',
            sa.text("regimen_fiscal IN ('GENERAL', 'PEQUENO_CONTRIBUYENTE')")
        )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # El camino inverso para rollbacks
    op.execute("UPDATE sat_libros SET regimen_fiscal = 'NORMAL' WHERE regimen_fiscal = 'GENERAL'")

    # Volvemos a limpiar preventivamente con IF EXISTS
    op.execute('ALTER TABLE sat_libros DROP CONSTRAINT IF EXISTS "regimenfiscal";')
    op.execute('ALTER TABLE sat_libros DROP CONSTRAINT IF EXISTS "sat_libros_regimen_fiscal_check";')

    with op.batch_alter_table('sat_libros', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'regimenfiscal',
            sa.text("regimen_fiscal IN ('NORMAL', 'PEQUENO_CONTRIBUYENTE')")
        )
    # ### end Alembic commands ###
