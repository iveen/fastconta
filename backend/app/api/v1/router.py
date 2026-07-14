from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
)
from app.api.v1.endpoints.base import (
    domicilios,
    empresas,
    representantes_legales,
    tenant_requests,
    tenants,
    users,
)
from app.api.v1.endpoints.catalogos import (
    actividades,
    catalogo_impuestos,
    categorias_activos,
    estados_libro,
    geografia,
    monedas,
    regimen_dte_config,
    regimenes_fiscales,
    tipo_persona,
    tipos_dte,
    tipos_libro,
)
from app.api.v1.endpoints.contabilidad import (
    activos_fijos,
    balances,
    cierre,
    partidas,
    periodos_fiscales,
    plan_cuentas,
)
from app.api.v1.endpoints.fel import facturas
from app.api.v1.endpoints.public import registration
from app.api.v1.endpoints.sat import (
    declaraciones,
    formularios_sat,
    reglas_filtrado,
    sat_libros,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(tenant_requests.router, tags=["solicitudes-registro"])
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
api_router.include_router(catalogo_impuestos.router)

api_router.include_router(tipos_dte.router)
api_router.include_router(regimen_dte_config.router)
api_router.include_router(actividades.router)
api_router.include_router(reglas_filtrado.router)
api_router.include_router(categorias_activos.router)
api_router.include_router(monedas.router)
api_router.include_router(geografia.router)
api_router.include_router(tipo_persona.router)
api_router.include_router(regimenes_fiscales.router)
api_router.include_router(domicilios.router)
api_router.include_router(representantes_legales.router)
api_router.include_router(tipos_libro.router)
api_router.include_router(estados_libro.router)
api_router.include_router(registration.router)
