

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CuentaCreate(BaseModel):
    codigo: str
    nombre: str
    tipo: Literal["activo", "pasivo", "patrimonio", "ingreso", "gasto"]
    naturaleza: Literal["deudora", "acreedora"]
    empresa_id: UUID 
    acepta_tercero: bool = False
    nivel: int = 1
    cuenta_padre_id: UUID | None  = None

class CuentaUpdate(BaseModel):
    nombre: str | None = None
    tipo: Literal["activo", "pasivo", "patrimonio", "ingreso", "gasto"] | None = None
    naturaleza: Literal["deudora", "acreedora"] | None = None
    empresa_id: UUID = None
    acepta_tercero: bool | None = None
    nivel: int | None = None
    cuenta_padre_id: UUID | None = None
    activa: bool | None = None

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