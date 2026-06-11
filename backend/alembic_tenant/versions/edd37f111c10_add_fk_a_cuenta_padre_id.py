"""add_FK a cuenta_padre_id

Revision ID: edd37f111c10
Revises: 3116febc6457
Create Date: 2026-06-09 17:55:44.824461

"""
import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'edd37f111c10'
down_revision: Union[str, None] = '3116febc6457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # Agregar Foreign Key a la columna existente cuenta_padre_id
    # La FK es autorreferencial: plan_cuentas.cuenta_padre_id -> plan_cuentas.id
    op.create_foreign_key(
        'fk_plan_cuentas_cuenta_padre_id',  # Nombre de la restricción
        'plan_cuentas',                      # Tabla origen
        'plan_cuentas',                      # Tabla destino (misma tabla)
        ['cuenta_padre_id'],                 # Columna origen
        ['id'],                              # Columna destino
        ondelete='SET NULL',                 # Si se elimina el padre, el hijo queda huérfano (NULL)
        use_alter=True                       # Necesario para FK autorreferenciales
    )


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # Eliminar la FK
    op.drop_constraint('fk_plan_cuentas_cuenta_padre_id', 'plan_cuentas', type_='foreignkey')
