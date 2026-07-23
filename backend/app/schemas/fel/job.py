from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FELImportJobResponse(BaseModel):
    """Respuesta con el estado de un job de importación FEL."""
    public_id: UUID
    estado: str
    archivo_original: str
    tamano_bytes: int
    archivos_totales: int = 0
    archivos_procesados: int = 0
    facturas_creadas: int = 0
    facturas_duplicadas: int = 0
    facturas_con_error: int = 0
    porcentaje: int = 0
    mensaje_error: str | None = None
    errores: list[dict] | None = None
    iniciado_en: datetime | None = None
    finalizado_en: datetime | None = None
    notificado: bool = False

    model_config = ConfigDict(from_attributes=True)


class FELJobCreatedResponse(BaseModel):
    """Respuesta al crear un job de importación FEL."""
    job_id: int
    public_id: UUID
    filename: str
    total_files: int
    estado: str
    message: str