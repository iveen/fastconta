from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class EmpresaCreate(BaseModel):
    nombre: str
    nit: str
    direccion: str | None = None

class EmpresaOut(BaseModel):
    id: UUID
    nombre: str
    nit: str
    direccion: str | None
    created_at: datetime