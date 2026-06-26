"""Schemas para Tipos de Persona"""

from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class TipoPersonaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, examples=["NATURAL"])


class TipoPersonaCreate(TipoPersonaBase):
    pass


class TipoPersonaUpdate(BaseModel):
    nombre: str | None = None


# ============================================================
# RESPONSE
# ============================================================
class TipoPersonaResponse(TipoPersonaBase):
    id: UUID

    model_config = {"from_attributes": True}


class TipoPersonaListResponse(BaseModel):
    id: UUID
    nombre: str

    model_config = {"from_attributes": True}