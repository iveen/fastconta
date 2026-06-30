from fastapi import APIRouter

from app.api.v1.endpoints import (
    actividades_economicas,
    activos_fijos,
    auth,
    balances,
    casillas_sat,
    categorias_activos,
    cierre,
    declaraciones,
    empresas,
    facturas,
    formularios_sat,
    geografia,
    monedas,
    partidas,
    periodos_fiscales,
    plan_cuentas,
    regimen_dte_config,
    regimenes_fiscales,
    reglas_filtrado,
    sat_libros,
    secciones_formulario,
    tenants,
    tipo_persona,
    tipos_dte,
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
api_router.include_router(activos_fijos.router)
api_router.include_router(declaraciones.router)
api_router.include_router(formularios_sat.router)
api_router.include_router(secciones_formulario.router)
api_router.include_router(casillas_sat.router)
api_router.include_router(tipos_dte.router)
api_router.include_router(regimen_dte_config.router)
api_router.include_router(actividades_economicas.router)
api_router.include_router(reglas_filtrado.router)
api_router.include_router(categorias_activos.router)
api_router.include_router(monedas.router)
api_router.include_router(geografia.router)
api_router.include_router(tipo_persona.router)
api_router.include_router(regimenes_fiscales.router)
