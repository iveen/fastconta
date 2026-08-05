"""add_es_exento_to_fel

Revision ID: 88c67bb670c8
Revises: 9af31ee0868c
Create Date: 2026-08-04 13:03:35.328639

Agrega el campo booleano `es_exento` a facturas_electronicas en todos
los schemas de tenant. Se deriva de total_exento > 0 en el clasificador.

Usado en las reglas de filtrado del SAT-2237 (casilla 3.1: Ventas exentas).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '88c67bb670c8'
down_revision: Union[str, None] = '9af31ee0868c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# CONFIGURACIÓN
# ============================================================
TABLA = "facturas_electronicas"
CAMPO = "es_exento"
INDICE = "idx_facturas_es_exento"


def _get_tenant_schemas() -> list[str]:
    """Retorna la lista de schemas de tenant (excluye schemas del sistema)."""
    conn = op.get_bind()
    result = conn.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('public', 'pg_catalog', 'information_schema')
          AND schema_name NOT LIKE 'pg\\_%'
          AND schema_name NOT LIKE '\\_timescaledb\\_%'
        ORDER BY schema_name
    """))
    return [row[0] for row in result]


def _tabla_existe_en_schema(schema: str) -> bool:
    """Verifica si la tabla facturas_electronicas existe en el schema dado."""
    conn = op.get_bind()
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = :tabla
        )
    """), {"schema": schema, "tabla": TABLA})
    return result.scalar()


def upgrade() -> None:
    """Agrega es_exento en todos los schemas de tenant."""
    schemas = _get_tenant_schemas()
    print(f"\n🔍 Schemas de tenant encontrados: {len(schemas)}")

    for schema in schemas:
        if not _tabla_existe_en_schema(schema):
            print(f"  ⏭️  {schema}: tabla '{TABLA}' no existe, saltando")
            continue

        print(f"  ➕ {schema}: agregando {CAMPO} a '{TABLA}'")

        # 1. Agregar columna booleana (NOT NULL, default false)
        op.add_column(
            TABLA,
            sa.Column(
                CAMPO,
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            schema=schema,
        )

        # 2. Crear índice para queries del motor SAT-2237
        # Nota: el nombre del índice incluye el schema para evitar colisiones
        # entre schemas (Alembic maneja esto automáticamente con schema=)
        op.create_index(
            INDICE,
            TABLA,
            [CAMPO],
            schema=schema,
        )

        print(f"  ✅ {schema}: campo e índice creados")

    print(f"\n✅ Migración completada en {len(schemas)} schemas")


def downgrade() -> None:
    """Elimina es_exento de todos los schemas de tenant."""
    schemas = _get_tenant_schemas()
    print(f"\n🔍 Schemas de tenant encontrados: {len(schemas)}")

    for schema in schemas:
        if not _tabla_existe_en_schema(schema):
            print(f"  ⏭️  {schema}: tabla '{TABLA}' no existe, saltando")
            continue

        print(f"  ➖ {schema}: eliminando {CAMPO} de '{TABLA}'")

        # 1. Eliminar índice primero
        op.drop_index(INDICE, table_name=TABLA, schema=schema)

        # 2. Eliminar columna
        op.drop_column(TABLA, CAMPO, schema=schema)

        print(f"  ✅ {schema}: campo e índice eliminados")

    print("\n✅ Rollback completado")
