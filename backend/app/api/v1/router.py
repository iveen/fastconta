from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    balances,
    cierre,
    empresas,
    facturas,
    partidas,
    periodos_fiscales,
    plan_cuentas,
    sat_libros,
    tenants,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["inquilinos"])
api_router.include_router(empresas.router, prefix="/empresas", tags=["empresas"])
api_router.include_router(plan_cuentas.router, prefix="/plan-cuentas", tags=["plan-cuentas"])
api_router.include_router(partidas.router, prefix="/partidas", tags=["partidas"])  
api_router.include_router(balances.router, prefix="/balances", tags=["balances"])
api_router.include_router(cierre.router, prefix="/cierre", tags=["cierre-contable"])
api_router.include_router(periodos_fiscales.router, prefix="/periodos-fiscales", tags=["periodos-fiscales"])
api_router.include_router(facturas.router, prefix="/facturas", tags=["facturas"])
api_router.include_router(sat_libros.router, prefix="/sat-libros", tags=["Libros SAT"])
api_router.include_router(users.router)


