#!/usr/bin/env python3
"""
Genera partidas contables de prueba para una empresa dentro de un tenant.

Uso:
    python seed_partidas.py <tenant_schema> <empresa_id> [--num 10]
"""

import asyncio
import sys
import uuid
import random
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select

from app.config import settings
from app.models.tenant_models import (
    CuentaContable, Partida, DetallePartida, PeriodoFiscal
)
from app.crud.secuencias import get_next_poliza

# ---------------------------------------------------------------------------
# Plantillas de transacciones típicas para una empresa comercial
TRANSACCIONES = [
    {
        "descripcion": "Venta de mercadería al contado",
        "detalles": [
            {"tipo_cuenta": "activo",    "codigo": "1.1.1", "movimiento": "debe"},   # Caja
            {"tipo_cuenta": "ingreso",   "codigo": "4.1",   "movimiento": "haber"},  # Ventas
        ]
    },
    {
        "descripcion": "Compra de inventario a crédito",
        "detalles": [
            {"tipo_cuenta": "activo",    "codigo": "1.1.3", "movimiento": "debe"},   # Inventarios
            {"tipo_cuenta": "pasivo",    "codigo": "2.1.1", "movimiento": "haber"},  # Proveedores
        ]
    },
    {
        "descripcion": "Pago de sueldos del mes",
        "detalles": [
            {"tipo_cuenta": "gasto",     "codigo": "5.2.1", "movimiento": "debe"},   # Sueldos
            {"tipo_cuenta": "activo",    "codigo": "1.1.1", "movimiento": "haber"},  # Caja
        ]
    },
    {
        "descripcion": "Cobro a clientes",
        "detalles": [
            {"tipo_cuenta": "activo",    "codigo": "1.1.1", "movimiento": "debe"},   # Caja
            {"tipo_cuenta": "activo",    "codigo": "1.1.2", "movimiento": "haber"},  # Cuentas por Cobrar
        ]
    },
    {
        "descripcion": "Pago de servicios básicos",
        "detalles": [
            {"tipo_cuenta": "gasto",     "codigo": "5.2.4", "movimiento": "debe"},   # Servicios Básicos
            {"tipo_cuenta": "activo",    "codigo": "1.1.1", "movimiento": "haber"},  # Caja
        ]
    },
    {
        "descripcion": "Pago de alquiler",
        "detalles": [
            {"tipo_cuenta": "gasto",     "codigo": "5.2.3", "movimiento": "debe"},   # Alquileres
            {"tipo_cuenta": "activo",    "codigo": "1.1.1", "movimiento": "haber"},  # Caja
        ]
    },
    {
        "descripcion": "Venta a crédito",
        "detalles": [
            {"tipo_cuenta": "activo",    "codigo": "1.1.2", "movimiento": "debe"},   # Cuentas por Cobrar
            {"tipo_cuenta": "ingreso",   "codigo": "4.1",   "movimiento": "haber"},  # Ventas
        ]
    },
    {
        "descripcion": "Aporte de capital de los socios",
        "detalles": [
            {"tipo_cuenta": "activo",    "codigo": "1.1.1", "movimiento": "debe"},   # Caja
            {"tipo_cuenta": "patrimonio","codigo": "3.1",   "movimiento": "haber"},  # Capital Social
        ]
    },
]

# ---------------------------------------------------------------------------
async def seed(schema_name: str, empresa_id: uuid.UUID, num_partidas: int = 10):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Obtener cuentas de la empresa (consulta cualificada)
        result = await session.execute(
            text(f"SELECT id, codigo FROM {schema_name}.plan_cuentas WHERE empresa_id = :emp_id AND activa = true"),
            {"emp_id": empresa_id}
        )
        cuentas_rows = result.fetchall()
        if not cuentas_rows:
            print(f"No hay cuentas para la empresa {empresa_id} en {schema_name}.")
            return

        cuentas_por_codigo = {row[1]: row[0] for row in cuentas_rows}

        # Obtener período fiscal abierto
        result_periodo = await session.execute(
            text(f"SELECT fecha_inicio, fecha_fin FROM {schema_name}.periodos_fiscales WHERE empresa_id = :emp_id AND cerrado = false LIMIT 1"),
            {"emp_id": empresa_id}
        )
        periodo = result_periodo.fetchone()
        if not periodo:
            print("No se encontró un período fiscal abierto para la empresa.")
            return

        fecha_inicio = periodo[0]
        fecha_fin = periodo[1]

        for i in range(num_partidas):
            t = random.choice(TRANSACCIONES)
            detalles = []
            for d in t["detalles"]:
                cuenta_id = cuentas_por_codigo.get(d["codigo"])
                if not cuenta_id:
                    print(f"  [!] Cuenta {d['codigo']} no encontrada, saltando.")
                    detalles = None
                    break
                monto = Decimal(str(random.randint(100, 2000)))
                detalles.append({
                    "cuenta_id": cuenta_id,
                    "tipo_movimiento": d["movimiento"],
                    "monto": monto
                })
            if not detalles:
                continue

            # Balancear con Caja si es necesario
            total_debe = sum(d["monto"] for d in detalles if d["tipo_movimiento"] == "debe")
            total_haber = sum(d["monto"] for d in detalles if d["tipo_movimiento"] == "haber")
            if total_debe != total_haber:
                cuenta_caja_id = cuentas_por_codigo.get("1.1.1")
                if not cuenta_caja_id:
                    print("  [!] No se encontró Caja para balancear.")
                    continue
                diff = total_debe - total_haber
                if diff > 0:
                    detalles.append({"cuenta_id": cuenta_caja_id, "tipo_movimiento": "haber", "monto": diff})
                else:
                    detalles.append({"cuenta_id": cuenta_caja_id, "tipo_movimiento": "debe", "monto": abs(diff)})

            # Generar número de póliza (la función get_next_poliza ya usa la tabla secuencias por empresa)
            numero_poliza = await get_next_poliza(session, empresa_id, schema_name)

            fecha_aleatoria = fecha_inicio + timedelta(days=random.randint(0, (fecha_fin - fecha_inicio).days))

            # Insertar partida con SQL cualificado
            insert_partida = text(f"""
                INSERT INTO {schema_name}.partidas (id, numero_poliza, fecha, descripcion, empresa_id)
                VALUES (gen_random_uuid(), :num_poliza, :fecha, :descripcion, :empresa_id)
                RETURNING id
            """)
            res = await session.execute(insert_partida, {
                "num_poliza": numero_poliza,
                "fecha": fecha_aleatoria,
                "descripcion": t["descripcion"],
                "empresa_id": empresa_id
            })
            partida_id = res.scalar_one()

            # Insertar detalles con SQL cualificado
            for det in detalles:
                await session.execute(
                    text(f"""INSERT INTO {schema_name}.detalle_partidas (id, partida_id, cuenta_id, tipo_movimiento, monto)
                             VALUES (gen_random_uuid(), :partida_id, :cuenta_id, :tipo, :monto)"""),
                    {"partida_id": partida_id, "cuenta_id": det["cuenta_id"], "tipo": det["tipo_movimiento"], "monto": det["monto"]}
                )

            print(f"  [{i+1}] {numero_poliza}: {t['descripcion']} ({fecha_aleatoria})")

        await session.commit()
        print(f"\nSe generaron {num_partidas} partidas de prueba en {schema_name} (empresa {empresa_id}).")

    await engine.dispose()

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Genera partidas contables de prueba.")
    parser.add_argument("tenant_schema", help="Nombre del schema del tenant")
    parser.add_argument("empresa_id", help="UUID de la empresa")
    parser.add_argument("--num", type=int, default=10, help="Número de partidas a generar")
    args = parser.parse_args()

    try:
        emp_id = uuid.UUID(args.empresa_id)
    except ValueError:
        print("El empresa_id debe ser un UUID válido.")
        sys.exit(1)

    asyncio.run(seed(args.tenant_schema, emp_id, args.num))