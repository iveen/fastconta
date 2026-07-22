from fastapi import APIRouter

from app.api.v1.endpoints.fel import facturas, jobs

router = APIRouter(prefix="/facturas", tags=["FEL"])

router.include_router(facturas.router, prefix="")
router.include_router(jobs.router, prefix="/jobs", tags=["FEL Jobs"])