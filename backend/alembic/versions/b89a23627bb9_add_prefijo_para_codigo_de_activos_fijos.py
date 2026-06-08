"""add prefijo para codigo de activos fijos

Revision ID: b89a23627bb9
Revises: 3a21c1582768
Create Date: 2026-06-05 18:38:27.102531

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b89a23627bb9'
down_revision: Union[str, None] = '3a21c1582768'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Agregar la columna (permitimos NULL temporalmente para no bloquear tablas con datos)
    op.add_column('categorias_activos_fijos', 
                  sa.Column('codigo_prefijo', sa.String(length=10), nullable=True))
    
    # 2. Actualizar los registros existentes con los prefijos correspondientes
    # Usamos un CASE SQL para hacer la actualización en una sola consulta
    op.execute(sa.text("""
        UPDATE categorias_activos_fijos
        SET codigo_prefijo = CASE
            WHEN nombre = 'Edificios y Construcciones' THEN 'EDIF'
            WHEN nombre = 'Plantaciones Agricolas' THEN 'PLAN'
            WHEN nombre = 'Mobiliario y Equipo de Oficina' THEN 'MOB'
            WHEN nombre = 'Maquinaria y Vehiculos' THEN 'VEH'
            WHEN nombre = 'Maquinaria y Equipo' THEN 'MAQ'
            WHEN nombre = 'Equipo de Computo' THEN 'COMP'
            WHEN nombre = 'Herramientas y Utensilios' THEN 'HERR'
            WHEN nombre = 'Ganado de Reproduccion' THEN 'GAN'
            WHEN nombre = 'Otros Bienes Muebles' THEN 'OTRO'
        END
    """))

    # 3. Hacer la columna no nula ahora que todos los datos están llenos
    op.alter_column('categorias_activos_fijos', 'codigo_prefijo', nullable=False)

    # 4. Agregar restricción de unicidad (para que no haya dos categorías con el mismo prefijo)
    # op.create_unique_constraint('uq_cat_activos_prefijo', 'categorias_activos_fijos', ['codigo_prefijo'])

def downgrade():
    # Eliminar restricción de unicidad primero
    op.drop_constraint('uq_cat_activos_prefijo', 'categorias_activos_fijos', type_='unique')
    # Eliminar columna
    op.drop_column('categorias_activos_fijos', 'codigo_prefijo')
