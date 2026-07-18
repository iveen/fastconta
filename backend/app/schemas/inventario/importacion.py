from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImportacionResponse(BaseModel):
    public_id: UUID
    toma_public_id: UUID
    archivo_original: str
    formato: str
    modo: str
    filas_procesadas: int
    filas_validas: int
    filas_con_error: int
    errores: list[dict] | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)