"""add_relacion_casilla_sat_declaracion

Revision ID: 333305a31fa5
Revises: 9ffed37a95d6
Create Date: 2026-06-15 16:06:57.310282

"""
import os
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '333305a31fa5'
down_revision: Union[str, None] = '9ffed37a95d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Skip para el tenant 'system' (esquema vacío para superadmin)
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # =========================================================================
    # NOTA: La relación 'casilla' en DetalleDeclaracionImpuesto es una relación
    # ORM pura (viewonly=True) que apunta a public.casillas_sat.
    # No requiere cambios en el esquema de la base de datos porque:
    # 1. La FK casilla_sat_id ya existe en la tabla detalles_declaracion_impuesto
    # 2. La tabla public.casillas_sat ya existe
    # 3. La relación usa primaryjoin explícito y viewonly=True
    #
    # Esta migración sirve como documentación del cambio en el modelo.
    # =========================================================================
    
    # Opcional: Agregar un índice para mejorar el rendimiento de la relación
    # (aunque la FK ya debería tener un índice implícito)
    # op.create_index(
    #     'idx_detalles_casilla_sat_id',
    #     'detalles_declaracion_impuesto',
    #     ['casilla_sat_id'],
    #     schema=tenant_schema
    # )
    pass


def downgrade() -> None:
    # Skip para el tenant 'system'
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # =========================================================================
    # No hay cambios que revertir porque la relación es solo ORM.
    # Si se agregó el índice opcional en upgrade(), descomentar esto:
    # =========================================================================
    
    # op.drop_index('idx_detalles_casilla_sat_id', table_name='detalles_declaracion_impuesto', schema=tenant_schema)
    pass
