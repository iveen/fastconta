"""refactor_casillas_sat

Revision ID: bc17f4792799
Revises: 2a0b13ebb02b
Create Date: 2026-06-16 13:13:27.887961

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bc17f4792799'
down_revision: Union[str, None] = '2a0b13ebb02b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar nuevos campos (permitiendo nulos temporalmente para migrar datos)
    op.add_column('casillas_sat', sa.Column('orden_seccion', sa.Integer, nullable=True))
    op.add_column('casillas_sat', sa.Column('tipo_casilla', sa.String(20), nullable=True))
    
    # 2. Migrar datos de las columnas antiguas a las nuevas
    op.execute("""
        UPDATE public.casillas_sat 
        SET orden_seccion = orden
    """)
    
    # Mapeo de tipo_valor a tipo_casilla
    op.execute("""
        UPDATE public.casillas_sat 
        SET tipo_casilla = CASE 
            WHEN tipo_valor IN ('BASE', 'IMPUESTO', 'TOTAL') THEN 'CALCULO'
            WHEN tipo_valor = 'INDICADOR' THEN 'INDICADOR'
            WHEN tipo_valor = 'RETENCION' THEN 'RETENCION'
            ELSE 'CALCULO'
        END
    """)
    
    # Casillas de la Sección 4 (Exportaciones) son REFERENCIA (no generan IVA)
    op.execute("""
        UPDATE public.casillas_sat 
        SET tipo_casilla = 'REFERENCIA'
        WHERE seccion = '4'
    """)

    # Casillas de la Sección 7 (Determinación) son CALCULADO
    op.execute("""
        UPDATE public.casillas_sat 
        SET tipo_casilla = 'CALCULADO'
        WHERE seccion = '7'
    """)

    # 3. Hacer los campos NOT NULL
    op.alter_column('casillas_sat', 'orden_seccion', nullable=False)
    op.alter_column('casillas_sat', 'tipo_casilla', nullable=False)
    
    # 4. Agregar restricciones e índices
    op.create_unique_constraint(
        'uq_casilla_seccion_orden', 
        'casillas_sat', 
        ['formulario_id', 'seccion', 'orden_seccion']
    )
    op.create_index(
        'idx_casillas_formulario_seccion', 
        'casillas_sat', 
        ['formulario_id', 'seccion']
    )
    
    # 5. Eliminar columnas antiguas
    op.drop_column('casillas_sat', 'orden')
    op.drop_column('casillas_sat', 'tipo_valor')


def downgrade() -> None:
    # Revertir cambios si es necesario
    op.add_column('casillas_sat', sa.Column('orden', sa.Integer, nullable=True))
    op.add_column('casillas_sat', sa.Column('tipo_valor', sa.String(20), nullable=True))
    
    op.execute("UPDATE public.casillas_sat SET orden = orden_seccion")
    op.execute("""
        UPDATE public.casillas_sat 
        SET tipo_valor = CASE 
            WHEN tipo_casilla = 'INDICADOR' THEN 'INDICADOR'
            WHEN tipo_casilla = 'RETENCION' THEN 'RETENCION'
            WHEN tipo_casilla = 'REFERENCIA' THEN 'BASE'
            ELSE 'IMPUESTO'
        END
    """)
    
    op.alter_column('casillas_sat', 'orden', nullable=False)
    op.alter_column('casillas_sat', 'tipo_valor', nullable=False)
    
    op.drop_column('casillas_sat', 'tipo_casilla')
    op.drop_column('casillas_sat', 'orden_seccion')
    
    op.drop_constraint('uq_casilla_seccion_orden', 'casillas_sat', type_='unique')
    op.drop_index('idx_casillas_formulario_seccion', table_name='casillas_sat')
