from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# 1. ESQUEMAS GLOBALES (Catálogos)
# Se usan para leer/configurar las categorías base de la SAT.
# ==============================================================================

class CategoriaActivoFijoBase(BaseModel):
    nombre: str = Field(..., max_length=100, description="Nombre del tipo de activo (Ej: Vehiculos, Edificios)")
    tasa_minima_anual: Decimal = Field(..., ge=0, le=100, description="Tasa minima anual permitida")
    tasa_maxima_anual: Decimal = Field(..., ge=0, le=100, description="Tasa maxima anual permitida (limite SAT)")
    vida_util_meses_default: int = Field(..., gt=0, description="Vida util en meses por defecto")
    is_active: bool = True

class CategoriaActivoFijoCreate(CategoriaActivoFijoBase):
    pass

class CategoriaActivoFijoUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=100)
    tasa_minima_anual: Decimal | None = Field(None, ge=0, le=100)
    tasa_maxima_anual: Decimal | None = Field(None, ge=0, le=100)
    vida_util_meses_default: int | None = Field(None, gt=0)
    is_active: bool | None = None

class CategoriaActivoFijoResponse(CategoriaActivoFijoBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 2. ESQUEMAS DEL TENANT (Activos y Depreciacion)
# ==============================================================================

# --- Sub-esquemas para respuestas enriquecidas (Nested) ---
class CuentaContableSimple(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    model_config = ConfigDict(from_attributes=True)

class CategoriaActivoFijoSimple(BaseModel):
    id: UUID
    nombre: str
    tasa_maxima_anual: Decimal
    model_config = ConfigDict(from_attributes=True)


# --- Activo Fijo ---
class ActivoFijoBase(BaseModel):
    codigo_interno: str = Field(..., max_length=50, description="Codigo interno de control (Ej: VEH-001)")
    descripcion: str = Field(..., max_length=255)
    fecha_adquisicion: date
    valor_costo: Decimal = Field(..., gt=0, description="Valor de adquisicion (factura + impuestos no recuperables)")
    valor_residual: Decimal = Field(default=0.0, ge=0, description="Valor de desecho estimado")
    tasa_depreciacion_anual_aplicada: Decimal = Field(..., gt=0, le=100, description="Porcentaje anual a aplicar")
    vida_util_meses_aplicada: int = Field(..., gt=0)
    
    # FKs
    categoria_id: UUID
    cuenta_gasto_id: UUID | None = Field(None, description="Si es nulo, se usa la cuenta por defecto de la categoria")
    cuenta_depreciacion_acumulada_id: UUID | None = Field(None, description="Si es nulo, se usa la cuenta por defecto de la categoria")
    estado: str = Field(default="activo", description="activo, totalmente_depreciado, dado_baja, vendido")

class ActivoFijoCreate(ActivoFijoBase):
    # empresa_id se inyecta desde el contexto del usuario autenticado en el servicio
    empresa_id: UUID | None = None 

class ActivoFijoUpdate(BaseModel):
    codigo_interno: str | None = Field(None, max_length=50)
    descripcion: str | None = Field(None, max_length=255)
    fecha_adquisicion: date | None = None
    valor_costo: Decimal | None = Field(None, gt=0)
    valor_residual: Decimal | None = Field(None, ge=0)
    tasa_depreciacion_anual_aplicada: Decimal | None = Field(None, gt=0, le=100)
    vida_util_meses_aplicada: int | None = Field(None, gt=0)
    categoria_id: UUID | None = None
    cuenta_gasto_id: UUID | None = None
    cuenta_depreciacion_acumulada_id: UUID | None = None
    estado: str | None = None

class ActivoFijoResponse(ActivoFijoBase):
    id: UUID
    empresa_id: UUID
    categoria: CategoriaActivoFijoSimple | None = None
    cuenta_gasto: CuentaContableSimple | None = None
    cuenta_depreciacion_acumulada: CuentaContableSimple | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Depreciación Activo (Histórico) ---
class DepreciacionActivoBase(BaseModel):
    anio_periodo: int = Field(..., ge=2000, le=2100)
    mes_periodo: int = Field(..., ge=1, le=12)
    monto_depreciacion_mes: Decimal = Field(..., ge=0)
    depreciacion_acumulada_hasta_fecha: Decimal = Field(..., ge=0)
    valor_en_libros: Decimal = Field(..., ge=0, description="valor_costo - depreciacion_acumulada_hasta_fecha")
    partida_id: UUID | None = Field(None, description="ID de la partida contable generada")

class DepreciacionActivoResponse(DepreciacionActivoBase):
    id: UUID
    activo_id: UUID
    empresa_id: UUID
    # Campos planos adicionales para facilitar la renderizacion en tablas del frontend
    activo_codigo: str | None = None
    activo_descripcion: str | None = None
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 3. ESQUEMAS DE ACCIÓN / PROCESOS (Cierre Mensual)
# ==============================================================================

class ProcesarDepreciacionMensualRequest(BaseModel):
    empresa_id: UUID
    anio_periodo: int = Field(..., ge=2000, le=2100)
    mes_periodo: int = Field(..., ge=1, le=12)

class ProcesarDepreciacionMensualResponse(BaseModel):
    exito: bool
    mensaje: str
    activos_procesados: int
    monto_total_depreciacion: Decimal
    partida_id_generada: UUID | None = Field(None, description="ID de la partida en estado 'Borrador' para revision")

class TablaDepreciacionProyectadaItem(BaseModel):
    anio_periodo: int
    mes_periodo: int
    monto_depreciacion_mes: Decimal
    depreciacion_acumulada_hasta_fecha: Decimal
    valor_en_libros: Decimal

class TablaDepreciacionProyectadaResponse(BaseModel):
    activo_id: UUID
    codigo_interno: str
    descripcion: str
    valor_costo: Decimal
    valor_residual: Decimal
    proyeccion: list[TablaDepreciacionProyectadaItem]