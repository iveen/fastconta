"""agrega_versionado_formularios_sat

Revision ID: fab74dec842a
Revises: 8947b657e7e3
Create Date: 2026-06-18 09:49:18.677842

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fab74dec842a'
down_revision: Union[str, None] = '8947b657e7e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # PASO 1: Agregar campos de versionado a formularios_sat
    # =========================================================================
    op.add_column(
        'formularios_sat',
        sa.Column('version', sa.String(10), nullable=False, server_default='1.0'),
        schema='public'
    )
    op.add_column(
        'formularios_sat',
        sa.Column('fecha_vigencia_desde', sa.Date(), nullable=False,
                  server_default=sa.text("CURRENT_DATE")),
        schema='public'
    )
    op.add_column(
        'formularios_sat',
        sa.Column('fecha_vigencia_hasta', sa.Date(), nullable=True),
        schema='public'
    )
    op.add_column(
        'formularios_sat',
        sa.Column('es_version_activa', sa.Boolean(), nullable=False,
                  server_default='true'),
        schema='public'
    )
    op.add_column(
        'formularios_sat',
        sa.Column('formulario_padre_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='public'
    )
    
    # =========================================================================
    # PASO 2: Manejar el constraint único de 'codigo'
    # =========================================================================
    # Primero dropeamos CUALQUIER constraint único existente sobre 'codigo'
    # porque el nombre puede variar según cómo se creó originalmente
    
    conn = op.get_bind()
    
    # Buscar todos los constraints únicos que involucren la columna 'codigo'
    result = conn.execute(sa.text("""
        SELECT conname 
        FROM pg_constraint 
        WHERE conrelid = 'public.formularios_sat'::regclass 
        AND contype = 'u'
        AND 'codigo'::text = ANY(
            ARRAY(
                SELECT pg_get_constraintdef(oid)::text 
                FROM pg_constraint 
                WHERE conrelid = 'public.formularios_sat'::regclass 
                AND contype = 'u'
            )
        )
    """))
    
    # Dropear todos los constraints únicos encontrados sobre 'codigo'
    for row in result:
        constraint_name = row[0]
        print(f"  🗑️  Dropeando constraint único: {constraint_name}")
        op.drop_constraint(
            constraint_name,
            'formularios_sat',
            schema='public',
            type_='unique'
        )
    
    # Ahora crear el nuevo constraint único compuesto (codigo + version)
    op.create_unique_constraint(
        'uq_formulario_codigo_version',
        'formularios_sat',
        ['codigo', 'version'],
        schema='public'
    )
    
    # =========================================================================
    # PASO 3: Crear índice para búsquedas por vigencia
    # =========================================================================
    op.create_index(
        'idx_formularios_vigencia',
        'formularios_sat',
        ['codigo', 'fecha_vigencia_desde', 'fecha_vigencia_hasta'],
        schema='public',
        unique=False
    )
    
    # =========================================================================
    # PASO 4: FK auto-referencial para versionado
    # =========================================================================
    op.create_foreign_key(
        'fk_formulario_padre',
        'formularios_sat', 'formularios_sat',
        ['formulario_padre_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # =========================================================================
    # PASO 1: Dropear FK auto-referencial
    # =========================================================================
    op.drop_constraint(
        'fk_formulario_padre',
        'formularios_sat',
        schema='public',
        type_='foreignkey'
    )
    
    # =========================================================================
    # PASO 2: Dropear índice de vigencia
    # =========================================================================
    op.drop_index(
        'idx_formularios_vigencia',
        'formularios_sat',
        schema='public'
    )
    
    # =========================================================================
    # PASO 3: Dropear constraint único compuesto
    # =========================================================================
    op.drop_constraint(
        'uq_formulario_codigo_version',
        'formularios_sat',
        schema='public',
        type_='unique'
    )
    
    # =========================================================================
    # PASO 4: Dropear columnas de versionado (en orden inverso)
    # =========================================================================
    op.drop_column('formularios_sat', 'formulario_padre_id', schema='public')
    op.drop_column('formularios_sat', 'es_version_activa', schema='public')
    op.drop_column('formularios_sat', 'fecha_vigencia_hasta', schema='public')
    op.drop_column('formularios_sat', 'fecha_vigencia_desde', schema='public')
    op.drop_column('formularios_sat', 'version', schema='public')