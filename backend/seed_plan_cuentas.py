#!/usr/bin/env python3
"""
Script para insertar un plan de cuentas contable básico en un tenant específico.

Uso:
    python seed_plan_cuentas.py <tenant_schema> <empresa_id>

Ejemplo:
    python seed_plan_cuentas.py tenant_contaguate 5dba429e-25c5-4cff-80f7-2dfa8446d022
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Ajustar el path para poder importar los módulos de la app
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.config import settings
from app.models.tenant_models import CuentaContable

# ---------------------------------------------------------------------------
CATALOGO = [
    # (código, nombre, tipo, naturaleza, nivel, código_padre)
    # NIVEL 1
    ("1",       "Activo",                "activo",      "deudora",   1, None),
    ("1.1",     "Activo Corriente",      "activo",      "deudora",   2, "1"),
    ("1.1.1",   "Caja y Bancos",         "activo",      "deudora",   3, "1.1"),
    ("1.1.2",   "Cuentas por Cobrar",    "activo",      "deudora",   3, "1.1"),
    ("1.1.3",   "Inventarios / Mercaderías", "activo",  "deudora",   3, "1.1"),
    ("1.1.4",   "IVA por Cobrar (Crédito Fiscal)", "activo", "deudora", 3, "1.1"),
    ("1.2",     "Activo No Corriente",   "activo",      "deudora",   2, "1"),
    ("1.2.1",   "Mobiliario y Equipo",   "activo",      "deudora",   3, "1.2"),
    ("1.2.2",   "Vehículos",             "activo",      "deudora",   3, "1.2"),
    ("1.2.3",   "Equipo de Computación", "activo",      "deudora",   3, "1.2"),

    ("2",       "Pasivo",                "pasivo",      "acreedora", 1, None),
    ("2.1",     "Pasivo Corriente",      "pasivo",      "acreedora", 2, "2"),
    ("2.1.1",   "Proveedores",           "pasivo",      "acreedora", 3, "2.1"),
    ("2.1.2",   "Cuentas por Pagar",     "pasivo",      "acreedora", 3, "2.1"),
    ("2.1.3",   "Impuestos por Pagar (IVA, ISR)", "pasivo", "acreedora", 3, "2.1"),
    ("2.1.4",   "Cuotas Laborales por Pagar (IGSS)", "pasivo", "acreedora", 3, "2.1"),
    ("2.2",     "Pasivo No Corriente",   "pasivo",      "acreedora", 2, "2"),
    ("2.2.1",   "Préstamos Bancarios a Largo Plazo", "pasivo", "acreedora", 3, "2.2"),

    ("3",       "Patrimonio / Capital",  "patrimonio", "acreedora", 1, None),
    ("3.1",     "Capital Social",        "patrimonio", "acreedora", 2, "3"),
    ("3.2",     "Reserva Legal",         "patrimonio", "acreedora", 2, "3"),
    ("3.3",     "Utilidades Retenidas",  "patrimonio", "acreedora", 2, "3"),
    ("3.4",     "Utilidad o Pérdida del Ejercicio", "patrimonio", "acreedora", 2, "3"),

    ("4",       "Ingresos",              "ingreso",     "acreedora", 1, None),
    ("4.1",     "Ingresos por Ventas / Servicios", "ingreso", "acreedora", 2, "4"),
    ("4.2",     "Ingresos Financieros",  "ingreso",     "acreedora", 2, "4"),
    ("4.3",     "Otros Ingresos",        "ingreso",     "acreedora", 2, "4"),

    ("5",       "Costos y Gastos",       "gasto",       "deudora",   1, None),
    ("5.1",     "Costo de Ventas",       "gasto",       "deudora",   2, "5"),
    ("5.2",     "Gastos de Operación / Administración", "gasto", "deudora", 2, "5"),
    ("5.2.1",   "Sueldos y Salarios",    "gasto",       "deudora",   3, "5.2"),
    ("5.2.2",   "Cuotas Patronales (IGSS)", "gasto",    "deudora",   3, "5.2"),
    ("5.2.3",   "Alquileres",            "gasto",       "deudora",   3, "5.2"),
    ("5.2.4",   "Servicios Básicos (Agua, luz, teléfono)", "gasto", "deudora", 3, "5.2"),
    ("5.2.5",   "Depreciaciones y Amortizaciones", "gasto", "deudora", 3, "5.2"),
]

# ---------------------------------------------------------------------------
async def seed(schema_name: str, empresa_id: uuid.UUID):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await session.execute(text(f"SET search_path TO {schema_name}, public"))

        # Mapa: código -> objeto CuentaContable
        cuentas_map = {}

        for codigo, nombre, tipo, naturaleza, nivel, codigo_padre in CATALOGO:
            padre_id = cuentas_map[codigo_padre].id if codigo_padre else None
            cuenta = CuentaContable(
                codigo=codigo,
                nombre=nombre,
                tipo=tipo,
                naturaleza=naturaleza,
                nivel=nivel,
                cuenta_padre_id=padre_id,
                empresa_id=empresa_id,
            )
            session.add(cuenta)
            await session.flush()  # para obtener el ID generado
            cuentas_map[codigo] = cuenta

        await session.commit()
        print(f"Plan de cuentas insertado correctamente en {schema_name} (empresa {empresa_id}).")

    await engine.dispose()

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python seed_plan_cuentas.py <tenant_schema> <empresa_id>")
        sys.exit(1)

    schema = sys.argv[1]
    try:
        emp_id = uuid.UUID(sys.argv[2])
    except ValueError:
        print("El empresa_id debe ser un UUID válido.")
        sys.exit(1)

    asyncio.run(seed(schema, emp_id))