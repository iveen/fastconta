"""add_campos_auditoria_catalogos

Revision ID: 62b673b5e008
Revises: 9ad4b0294844
Create Date: 2026-07-02 13:12:37.380760

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '62b673b5e008'
down_revision: Union[str, None] = '9ad4b0294844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = 'public'

# Clasificación de tablas según qué columnas ya tienen
# (tabla, tiene_created_at, tiene_updated_at)
TABLAS = {
    'catalogo_monedas':            (True,  True),
    'actividades_economicas_sat':  (True,  False),
    'tipos_persona':               (False, False),
    'departamentos':               (False, False),
    'municipios':                  (False, False),
    'categorias_activos_fijos':    (True,  False),
}

# Tablas con bug UUID (VARCHAR → UUID nativo)
TABLAS_FIX_UUID = []


def _inspector():
    return sa.inspect(op.get_bind())


def _add_timestamp(table: str, col: str, nullable: bool, with_default: bool = False) -> None:
    kwargs = {'nullable': nullable}
    if with_default:
        kwargs['server_default'] = sa.func.now()
    op.add_column(table, sa.Column(col, sa.DateTime(timezone=True), **kwargs), schema=SCHEMA)
    op.create_index(f'ix_{table}_{col}', table, [col], schema=SCHEMA)


def _add_user_fk(table: str, col: str, comment: str) -> None:
    op.add_column(
        table,
        sa.Column(
            col,
            UUID(as_uuid=True),
            sa.ForeignKey(f'{SCHEMA}.users.id', ondelete='SET NULL'),
            nullable=True,
            comment=comment,
        ),
        schema=SCHEMA,
    )
    op.create_index(f'ix_{table}_{col}', table, [col], schema=SCHEMA)


def _fix_uuid_column(table: str, col: str) -> None:
    """Convierte VARCHAR → UUID nativo en PostgreSQL."""
    # 1. Crear columna temporal UUID
    op.add_column(
        table,
        sa.Column(f'{col}_new', UUID(as_uuid=True), nullable=True),
        schema=SCHEMA,
    )
    # 2. Copiar datos (cast de string a UUID)
    op.execute(f"""
        UPDATE {SCHEMA}.{table}
        SET {col}_new = CAST({col} AS UUID)
        WHERE {col} IS NOT NULL
    """)
    # 3. Eliminar índices/dependencias de la columna vieja
    # (los FK se recrean después si es necesario)
    op.drop_column(table, col, schema=SCHEMA)
    # 4. Renombrar
    op.alter_column(
        table, f'{col}_new',
        new_column_name=col,
        schema=SCHEMA,
    )


def upgrade() -> None:
    # ============================================================
    # 1. Agregar columnas de auditoría según estado actual
    # ============================================================
    for table, (has_created, has_updated) in TABLAS.items():
        if not has_created:
            _add_timestamp(table, 'created_at', nullable=False, with_default=True)
        if not has_updated:
            _add_timestamp(table, 'updated_at', nullable=True)

        # *_by siempre se agregan (ninguna tabla los tenía)
        _add_user_fk(table, 'created_by', 'Usuario que creó el registro')
        _add_user_fk(table, 'updated_by', 'Usuario que modificó el registro por última vez')

    # ============================================================
    # 2. Corregir bug UUID en 3 tablas
    # ============================================================
    for table in TABLAS_FIX_UUID:
        _fix_uuid_column(table, 'id')

        # Si es 'municipios', también corregir departamento_id (FK)
        if table == 'municipios':
            _fix_uuid_column(table, 'departamento_id')


def downgrade() -> None:
    # ============================================================
    # 1. Revertir bug fix UUID (UUID → VARCHAR)
    # ============================================================
    for table in reversed(TABLAS_FIX_UUID):
        if table == 'municipios':
            _fix_uuid_column_revert(table, 'departamento_id')
        _fix_uuid_column_revert(table, 'id')

    # ============================================================
    # 2. Eliminar columnas de auditoría
    # ============================================================
    for table in reversed(list(TABLAS.keys())):
        op.drop_index(f'ix_{table}_updated_by', table_name=table, schema=SCHEMA)
        op.drop_index(f'ix_{table}_created_by', table_name=table, schema=SCHEMA)
        op.drop_column(table, 'updated_by', schema=SCHEMA)
        op.drop_column(table, 'created_by', schema=SCHEMA)

        has_created, has_updated = TABLAS[table]
        if not has_updated:
            op.drop_index(f'ix_{table}_updated_at', table_name=table, schema=SCHEMA)
            op.drop_column(table, 'updated_at', schema=SCHEMA)
        if not has_created:
            op.drop_index(f'ix_{table}_created_at', table_name=table, schema=SCHEMA)
            op.drop_column(table, 'created_at', schema=SCHEMA)


def _fix_uuid_column_revert(table: str, col: str) -> None:
    """Revierte UUID nativo → VARCHAR (para downgrade)."""
    op.add_column(
        table,
        sa.Column(f'{col}_old', sa.String(36), nullable=True),
        schema=SCHEMA,
    )
    op.execute(f"""
        UPDATE {SCHEMA}.{table}
        SET {col}_old = CAST({col} AS VARCHAR)
        WHERE {col} IS NOT NULL
    """)
    op.drop_column(table, col, schema=SCHEMA)
    op.alter_column(
        table, f'{col}_old',
        new_column_name=col,
        schema=SCHEMA,
    )
