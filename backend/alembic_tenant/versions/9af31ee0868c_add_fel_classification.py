"""add_fel_classification

Revision ID: 9af31ee0868c
Revises: aa88ec971526
Create Date: 2026-08-03 13:44:15.022908

Agrega campos de clasificación denormalizados a facturas_electronicas
para optimizar las reglas de filtrado del motor de declaraciones SAT.

Campos agregados:
  - es_medicamento: bool (indexado)
  - es_vehiculo: bool (indexado)
  - es_vehiculo_usado: bool
  - es_vehiculo_nuevo: bool
  - es_pequeno_contribuyente: bool (indexado)
  - es_no_afecta: bool
  - no_genera_credito_fiscal: bool
  - tiene_constancia_exencion: bool
  - region_destino: varchar(20) (indexado) → LOCAL | CENTROAMERICA | RESTO_MUNDO
  - bien_o_servicio_predominante: varchar(1) → B | S | M

⚠️ Multi-tenant: se aplica en TODOS los schemas de tenant.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9af31ee0868c'
down_revision: Union[str, None] = 'aa88ec971526'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# CONFIGURACIÓN
# ============================================================
TABLA = "facturas_electronicas"

# Campos booleanos con server_default='false'
CAMPOS_BOOLEANOS = [
    ("es_medicamento", False),
    ("es_vehiculo", False),
    ("es_vehiculo_usado", False),
    ("es_vehiculo_nuevo", False),
    ("es_pequeno_contribuyente", False),
    ("es_no_afecta", False),
    ("no_genera_credito_fiscal", False),
    ("tiene_constancia_exencion", False),
]

# Campos string (nullable, sin default)
CAMPOS_STRING = [
    ("region_destino", 20),              # LOCAL | CENTROAMERICA | RESTO_MUNDO
    ("bien_o_servicio_predominante", 1), # B | S | M
]

# Índices a crear (campo → nombre del índice)
INDICES = {
    "es_medicamento": "idx_facturas_es_medicamento",
    "es_vehiculo": "idx_facturas_es_vehiculo",
    "es_pequeno_contribuyente": "idx_facturas_es_pc",
    "region_destino": "idx_facturas_region_destino",
}


def _get_tenant_schemas() -> list[str]:
    """
    Retorna la lista de schemas de tenant (excluye schemas del sistema
    y el schema public que no contiene facturas_electronicas).
    """
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
    """Agrega campos de clasificación en todos los schemas de tenant."""
    schemas = _get_tenant_schemas()
    print(f"\n🔍 Schemas de tenant encontrados: {len(schemas)}")

    for schema in schemas:
        # Saltar schemas que no tienen la tabla (ej: schemas de soporte)
        if not _tabla_existe_en_schema(schema):
            print(f"  ⏭️  {schema}: tabla '{TABLA}' no existe, saltando")
            continue

        print(f"  ➕ {schema}: agregando campos a '{TABLA}'")

        # --------------------------------------------------
        # 1. Agregar campos booleanos
        # --------------------------------------------------
        for campo, es_indexado in CAMPOS_BOOLEANOS:
            op.add_column(
                TABLA,
                sa.Column(
                    campo,
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("false"),
                ),
                schema=schema,
            )

        # --------------------------------------------------
        # 2. Agregar campos string (nullable)
        # --------------------------------------------------
        for campo, longitud in CAMPOS_STRING:
            op.add_column(
                TABLA,
                sa.Column(
                    campo,
                    sa.String(length=longitud),
                    nullable=True,
                ),
                schema=schema,
            )

        # --------------------------------------------------
        # 3. Crear índices
        # --------------------------------------------------
        for campo, nombre_indice in INDICES.items():
            op.create_index(
                nombre_indice,
                TABLA,
                [campo],
                schema=schema,
            )

        print(f"  ✅ {schema}: campos e índices creados")

    print(f"\n✅ Migración completada en {len(schemas)} schemas")


def downgrade() -> None:
    """Elimina los campos de clasificación de todos los schemas de tenant."""
    schemas = _get_tenant_schemas()
    print(f"\n🔍 Schemas de tenant encontrados: {len(schemas)}")

    for schema in schemas:
        if not _tabla_existe_en_schema(schema):
            print(f"  ⏭️  {schema}: tabla '{TABLA}' no existe, saltando")
            continue

        print(f"  ➖ {schema}: eliminando campos de '{TABLA}'")

        # --------------------------------------------------
        # 1. Eliminar índices primero (antes que las columnas)
        # --------------------------------------------------
        for campo, nombre_indice in INDICES.items():
            op.drop_index(
                nombre_indice,
                table_name=TABLA,
                schema=schema,
            )

        # --------------------------------------------------
        # 2. Eliminar campos string
        # --------------------------------------------------
        for campo, _ in CAMPOS_STRING:
            op.drop_column(TABLA, campo, schema=schema)

        # --------------------------------------------------
        # 3. Eliminar campos booleanos
        # --------------------------------------------------
        for campo, _ in CAMPOS_BOOLEANOS:
            op.drop_column(TABLA, campo, schema=schema)

        print(f"  ✅ {schema}: campos e índices eliminados")

    print(f"\n✅ Rollback completado en {len(schemas)} schemas")
