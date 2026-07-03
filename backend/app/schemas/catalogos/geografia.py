"""Schemas para Geografía (Departamentos y Municipios)"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MunicipioBrief(BaseModel):
    id: UUID
    codigo_iso: str
    nombre: str
    
    model_config = {"from_attributes": True}


# ============================================================
# DEPARTAMENTO
# ============================================================
class DepartamentoBase(BaseModel):
    codigo_iso: str = Field(..., min_length=2, max_length=2, examples=["01"])
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Guatemala"])


class DepartamentoCreate(DepartamentoBase):
    pass


class DepartamentoUpdate(BaseModel):
    nombre: str | None = None


class DepartamentoResponse(DepartamentoBase):
    id: UUID
    municipios: list[MunicipioBrief] = []  
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


# ============================================================
# MUNICIPIO
# ============================================================
class MunicipioBase(BaseModel):
    codigo_iso: str = Field(..., min_length=4, max_length=4, examples=["0101"])
    nombre: str = Field(..., min_length=1, max_length=100)
    departamento_id: UUID


class MunicipioCreate(MunicipioBase):
    pass




class MunicipioUpdate(BaseModel):
    nombre: str | None = None
    departamento_id: UUID | None = None


class MunicipioResponse(MunicipioBase):
    id: UUID
    departamento_nombre: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}