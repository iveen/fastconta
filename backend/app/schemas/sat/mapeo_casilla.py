"""Schemas para Mapeo Casilla-Cuenta"""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

TIPOS_MOVIMIENTO = ["DEBE", "HABER"]


# ============================================================
# BASE
# ============================================================
class MapeoCasillaCuentaBase(BaseModel):
    casilla_id: UUID
    tenant_id: UUID | None = None
    empresa_id: UUID | None = None
    codigo_cuenta_sugerido: str = Field(..., min_length=1, max_length=20)
    nombre_cuenta_sugerido: str = Field(..., min_length=1, max_length=255)
    tipo_movimiento: str = Field(..., min_length=4, max_length=10)

    @field_validator("tipo_movimiento")
    @classmethod
    def validar_tipo_movimiento(cls, v: str) -> str:
        if v not in TIPOS_MOVIMIENTO:
            raise ValueError(f"tipo_movimiento debe ser uno de {TIPOS_MOVIMIENTO}")
        return v.upper()


class MapeoCasillaCuentaCreate(MapeoCasillaCuentaBase):
    pass


class MapeoCasillaCuentaUpdate(BaseModel):
    tenant_id: UUID | None = None
    empresa_id: UUID | None = None
    codigo_cuenta_sugerido: str | None = None
    nombre_cuenta_sugerido: str | None = None
    tipo_movimiento: str | None = None


# ============================================================
# RESPONSE
# ============================================================
class MapeoCasillaCuentaResponse(MapeoCasillaCuentaBase):
    id: UUID
    casilla_codigo: str | None = None
    casilla_nombre: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class MapeoCasillaCuentaListResponse(BaseModel):
    id: UUID
    casilla_id: UUID
    casilla_codigo: str | None = None
    tenant_id: UUID | None = None
    empresa_id: UUID | None = None
    codigo_cuenta_sugerido: str
    tipo_movimiento: str

    model_config = {"from_attributes": True}


# ============================================================
# IMPORT/EXPORT
# ============================================================
class MapeoImportItem(BaseModel):
    codigo_casilla: str = Field(..., min_length=1)
    codigo_cuenta_sugerido: str = Field(..., min_length=1, max_length=20)
    nombre_cuenta_sugerido: str = Field(..., min_length=1, max_length=255)
    tipo_movimiento: str = Field(..., min_length=4, max_length=10)
    ambito: str | None = Field("GLOBAL", description="GLOBAL, TENANT o EMPRESA")


class MapeoImportResult(BaseModel):
    """Resultado de importación"""
    creados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: list[str] = []