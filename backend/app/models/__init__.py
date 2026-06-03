# app/models/__init__.py
# Este archivo es CRÍTICO para resolver dependencias circulares en SQLAlchemy.
# Fuerza el orden de importación: primero los modelos globales, luego los de tenant.

# 1. Importar primero los modelos globales (esquema public)
from app.models.global_models import (
    ActividadEconomicaSAT,
    CatalogoImpuestoEspecial,
    CatalogoMoneda,
    CategoriaActivoFijo,
    Departamento,
    EstadoActivoFijoEnum,
    EstadoLibro,
    Municipio,
    RegimenFiscal,
    Role,
    Tenant,
    TipoDomicilio,
    TipoDTE,
    TipoLibro,
    TipoPersona,
    User,
    UserEmpresa,
)

# 2. Importar después los modelos del tenant (dependen de los globales)
from app.models.tenant_models import (
    ActivoFijo,
    CuentaContable,
    DepreciacionActivo,
    DetallePartida,
    Domicilio,
    Empresa,
    FacturaDetalle,
    FacturaElectronica,
    FacturaImpuestoEspecial,
    Partida,
    PeriodoFiscal,
    RepresentanteLegal,
    SatLibro,
    SatLibroLinea,
    Secuencia,
)
