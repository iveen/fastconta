from fastapi import APIRouter
from app.api.v1.endpoints import auth, tenants, empresas, plan_cuentas, partidas, balances, cierre

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(empresas.router, prefix="/empresas", tags=["empresas"])
api_router.include_router(plan_cuentas.router, prefix="/plan-cuentas", tags=["plan-cuentas"])
api_router.include_router(partidas.router, prefix="/partidas", tags=["partidas"])  
api_router.include_router(balances.router, prefix="/balances", tags=["balances"])
api_router.include_router(cierre.router, prefix="/cierre", tags=["cierre-contable"])