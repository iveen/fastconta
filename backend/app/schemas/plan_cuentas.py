# app/schemas/plan_cuentas.py
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CuentaCreate(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=255)
    tipo: Literal["activo", "pasivo", "patrimonio", "ingreso", "gasto"]
    naturaleza: Literal["deudora", "acreedora"]
    empresa_id: UUID
    acepta_tercero: bool = False
    nivel: int = Field(default=1, ge=1, le=10)
    cuenta_padre_id: UUID | None = None

class CuentaUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=255)
    tipo: Literal["activo", "pasivo", "patrimonio", "ingreso", "gasto"] | None = None
    naturaleza: Literal["deudora", "acreedora"] | None = None
    acepta_tercero: bool | None = None
    nivel: int | None = Field(default=None, ge=1, le=10)
    cuenta_padre_id: UUID | None = None
    activa: bool | None = None
    # NOTA: Se elimina empresa_id de Update para evitar movimientos accidentales entre empresas

class CuentaOut(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    tipo: str
    naturaleza: str
    acepta_tercero: bool
    nivel: int
    cuenta_padre_id: UUID | None = None
    activa: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Esquema exclusivo para validar filas del Excel
class CuentaImportRow(BaseModel):
    codigo: str
    nombre: str
    tipo: Literal["activo", "pasivo", "patrimonio", "ingreso", "gasto"]
    naturaleza: Literal["deudora", "acreedora"]
    nivel: int
    cuenta_padre_codigo: str | None = None
    acepta_tercero: bool = False