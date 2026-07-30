from fastapi import APIRouter

from app.api.v1.endpoints.fel import facturas, jobs, kpis

router = APIRouter(prefix="/facturas", tags=["FEL"])

# 1. Rutas específicas (sin parámetros comodín) van PRIMERO
router.include_router(kpis.router, prefix="", tags=["FEL KPIS"])
router.include_router(jobs.router, prefix="/jobs", tags=["FEL Jobs"])

# 2. Rutas con parámetros comodín (/{factura_id}) van AL FINAL
# Esto evita que "kpis" o "jobs" sean interpretados como un factura_id
router.include_router(facturas.router, prefix="")
