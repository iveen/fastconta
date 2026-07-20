from fastapi import APIRouter

from app.api.v1.endpoints.inventario import (
    bodegas,
    costo_ventas,
    export,
    importacion,
    items,
    jobs,  # ✅ NUEVO
    productos,
    tomas,
)

router = APIRouter(prefix="/inventarios", tags=["Inventarios"])

router.include_router(bodegas.router, prefix="/bodegas")
router.include_router(productos.router, prefix="/productos")
router.include_router(tomas.router, prefix="/tomas")
router.include_router(items.router, prefix="/items")
router.include_router(importacion.router, prefix="/importaciones")
router.include_router(jobs.router, prefix="/importaciones")  
router.include_router(costo_ventas.router, prefix="/costo-ventas")
router.include_router(export.router, prefix="/export")