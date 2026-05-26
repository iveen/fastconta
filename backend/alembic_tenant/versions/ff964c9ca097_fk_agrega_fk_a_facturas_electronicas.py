"""fk: agrega fk a facturas_electronicas

Revision ID: ff964c9ca097
Revises: bdac449affae
Create Date: 2026-05-25 18:14:42.092174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff964c9ca097'
down_revision: Union[str, None] = 'bdac449affae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar las columnas de IDs
    op.add_column('facturas_electronicas', sa.Column('tipo_documento_id', sa.UUID(as_uuid=True), nullable=True))
    op.add_column('facturas_electronicas', sa.Column('moneda_id', sa.UUID(as_uuid=True), nullable=True))
    
    # 2. Crear Foreign Keys apuntando al esquema GLOBAL 'public'
    # Esto conecta las tablas del tenant con los catálogos compartidos
    
    # FK hacia tipos_dte
    op.create_foreign_key(
        'fk_facturas_tipos_dte',             # Nombre de la restricción
        'facturas_electronicas',             # Tabla origen (Tenant)
        'tipos_dte',                         # Tabla destino (Public)
        ['tipo_documento_id'],               # Columna local
        ['id'],                              # Columna remota
        referent_schema='public'             # 🔑 CRÍTICO: Indica que la tabla destino está en 'public'
    )

    # FK hacia catalogo_monedas
    op.create_foreign_key(
        'fk_facturas_catalogo_monedas',      # Nombre de la restricción
        'facturas_electronicas',             # Tabla origen (Tenant)
        'catalogo_monedas',                  # Tabla destino (Public)
        ['moneda_id'],                       # Columna local
        ['id'],                              # Columna remota
        referent_schema='public'             # 🔑 CRÍTICO
    )

    # Opcional: Crear índices para mejorar rendimiento en las búsquedas
    op.create_index('ix_facturas_electronicas_tipo_documento_id', 'facturas_electronicas', ['tipo_documento_id'], unique=False)
    op.create_index('ix_facturas_electronicas_moneda_id', 'facturas_electronicas', ['moneda_id'], unique=False)

def downgrade() -> None:
    # Eliminar en orden inverso: primero restricciones, luego columnas
    
    op.drop_constraint('fk_facturas_catalogo_monedas', 'facturas_electronicas', type_='foreignkey')
    op.drop_column('facturas_electronicas', 'moneda_id')
    
    op.drop_constraint('fk_facturas_tipos_dte', 'facturas_electronicas', type_='foreignkey')
    op.drop_column('facturas_electronicas', 'tipo_documento_id')
