"""Schemas para Regímenes Fiscales"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class RegimenFiscalBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, examples=["PC_FEL"])
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Pequeño Contribuyente Electrónico (FEL)"])
    descripcion: str | None = Field(None, examples=["Art. 45 Dec. 10-2012. 4% mensual."])
    is_active: bool = True


class RegimenFiscalCreate(RegimenFiscalBase):
    pass


class RegimenFiscalUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    is_active: bool | None = None


# ============================================================
# RESPONSE (con auditoría completa)
# ============================================================
class RegimenFiscalResponse(RegimenFiscalBase):
    id: UUID
    # Auditoría completa
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class RegimenFiscalListResponse(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None = None
    is_active: bool
    # Auditoría mínima para listados
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ============================================================
# RESPONSE CON FORMULARIOS ASOCIADOS
# ============================================================
class FormularioAsociadoBrief(BaseModel):
    id: UUID
    codigo: str
    version: str
    nombre: str
    es_obligatorio: bool = True

    model_config = {"from_attributes": True}


class RegimenFiscalDetailResponse(RegimenFiscalResponse):
    """Respuesta detallada con formularios SAT asociados"""
    formularios_asociados: list[FormularioAsociadoBrief] = []