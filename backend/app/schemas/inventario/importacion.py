from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImportacionJobResponse(BaseModel):
    """Respuesta con el estado de un job de importación."""
    public_id: UUID
    estado: str
    archivo_original: str
    tamano_bytes: int
    filas_totales: int = 0
    filas_procesadas: int = 0
    filas_validas: int = 0
    filas_con_error: int = 0
    porcentaje: int = 0
    mensaje_error: str | None = None
    importacion_public_id: str | None = None
    iniciado_en: datetime | None = None
    finalizado_en: datetime | None = None
    mensaje: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ImportacionResponse(BaseModel):
    """Respuesta con el detalle de una importación completada."""
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