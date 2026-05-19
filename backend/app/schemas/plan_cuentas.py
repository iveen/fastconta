from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

class CuentaCreate(BaseModel):
    codigo: str
    nombre: str
    tipo: Literal["activo", "pasivo", "patrimonio", "ingreso", "gasto"]
    naturaleza: Literal["deudora", "acreedora"]
    empresa_id: UUID 
    acepta_tercero: bool = False
    nivel: int = 1
    cuenta_padre_id: Optional[UUID] = None

class CuentaUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[Literal["activo", "pasivo", "patrimonio", "ingreso", "gasto"]] = None
    naturaleza: Optional[Literal["deudora", "acreedora"]] = None
    empresa_id: UUID = None
    acepta_tercero: Optional[bool] = None
    nivel: Optional[int] = None
    cuenta_padre_id: Optional[UUID] = None
    activa: Optional[bool] = None

class CuentaOut(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    tipo: str
    naturaleza: str
    acepta_tercero: bool
    nivel: int
    cuenta_padre_id: Optional[UUID]
    activa: bool
    created_at: datetime