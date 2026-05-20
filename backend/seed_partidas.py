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
        await session.execute(text(f"SET search_path TO {schema_name}, public"))

        # Obtener cuentas de la empresa
        result = await session.execute(
            select(CuentaContable).where(
                CuentaContable.empresa_id == empresa_id,
                CuentaContable.activa == True
            )
        )
        cuentas = result.scalars().all()

        if not cuentas:
            print(f"No hay cuentas para la empresa {empresa_id} en {schema_name}.")
            return

        # Mapa código -> cuenta
        cuentas_por_codigo = {c.codigo: c for c in cuentas}

        # Obtener período fiscal abierto para esta empresa
        result_periodo = await session.execute(
            select(PeriodoFiscal).where(
                PeriodoFiscal.empresa_id == empresa_id,
                PeriodoFiscal.cerrado == False
            )
        )
        periodo = result_periodo.scalar_one_or_none()
        if not periodo:
            print("No se encontró un período fiscal abierto para la empresa.")
            return

        fecha_inicio = periodo.fecha_inicio
        fecha_fin = periodo.fecha_fin

        for i in range(num_partidas):
            # Elegir una transacción al azar
            t = random.choice(TRANSACCIONES)

            # Construir detalles usando los códigos de cuentas
            detalles = []
            for d in t["detalles"]:
                codigo = d["codigo"]
                cuenta = cuentas_por_codigo.get(codigo)
                if not cuenta:
                    print(f"  [!] Cuenta {codigo} no encontrada, saltando transacción.")
                    detalles = None
                    break
                monto = Decimal(str(random.randint(100, 2000)))  # Monto aleatorio entre 100 y 2000
                detalles.append({
                    "cuenta_id": cuenta.id,
                    "tipo_movimiento": d["movimiento"],
                    "monto": monto
                })
            if not detalles:
                continue

            # Asegurar partida doble: sumas iguales
            debe = sum(d["monto"] for d in detalles if d["tipo_movimiento"] == "debe")
            haber = sum(d["monto"] for d in detalles if d["tipo_movimiento"] == "haber")
            # Si no cuadra, ajustamos el último detalle (o añadimos diferencia)
            if debe != haber:
                diff = debe - haber
                # Buscamos el último detalle y le ajustamos el monto
                last = detalles[-1]
                last["monto"] += abs(diff)

            # Fecha aleatoria dentro del período fiscal
            dias_rango = (fecha_fin - fecha_inicio).days
            fecha_aleatoria = fecha_inicio + timedelta(days=random.randint(0, dias_rango))

            # Generar número de póliza usando la función del sistema
            numero_poliza = await get_next_poliza(session, empresa_id)

            partida = Partida(
                fecha=fecha_aleatoria,
                descripcion=t["descripcion"],
                numero_poliza=numero_poliza,
            )
            session.add(partida)
            await session.flush()

            for det in detalles:
                session.add(DetallePartida(
                    partida_id=partida.id,
                    cuenta_id=det["cuenta_id"],
                    tipo_movimiento=det["tipo_movimiento"],
                    monto=det["monto"]
                ))

            print(f"  [{i+1}] {partida.numero_poliza}: {partida.descripcion} ({partida.fecha})")

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