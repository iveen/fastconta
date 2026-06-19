"""Schemas para Geografía (Departamentos y Municipios de Guatemala)"""

from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# DEPARTAMENTO - BASE
# ============================================================
class DepartamentoBase(BaseModel):
    codigo_iso: str = Field(
        ...,
        min_length=2,
        max_length=2,
        examples=["AV"],
        description="Código ISO de 2 caracteres (ej: AV=Alta Verapaz, GU=Guatemala)",
    )
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Alta Verapaz"])


class DepartamentoCreate(DepartamentoBase):
    pass


class DepartamentoUpdate(BaseModel):
    nombre: str | None = None


# ============================================================
# DEPARTAMENTO - RESPONSE
# ============================================================
class DepartamentoResponse(DepartamentoBase):
    id: UUID
    total_municipios: int = 0

    model_config = {"from_attributes": True}


class DepartamentoListResponse(BaseModel):
    id: UUID
    codigo_iso: str
    nombre: str
    total_municipios: int = 0

    model_config = {"from_attributes": True}


# ============================================================
# MUNICIPIO - BASE
# ============================================================
class MunicipioBase(BaseModel):
    codigo_iso: str = Field(
        ...,
        min_length=4,
        max_length=4,
        examples=["0101"],
        description="Código ISO de 4 caracteres (2 dept + 2 municipio)",
    )
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Cobán"])
    departamento_id: UUID


class MunicipioCreate(MunicipioBase):
    pass


class MunicipioUpdate(BaseModel):
    nombre: str | None = None
    departamento_id: UUID | None = None


# ============================================================
# MUNICIPIO - RESPONSE
# ============================================================
class MunicipioResponse(MunicipioBase):
    id: UUID
    departamento_nombre: str | None = None
    departamento_codigo: str | None = None

    model_config = {"from_attributes": True}


class MunicipioListResponse(BaseModel):
    id: UUID
    codigo_iso: str
    nombre: str
    departamento_id: UUID
    departamento_nombre: str | None = None

    model_config = {"from_attributes": True}


# ============================================================
# IMPORT/EXPORT
# ============================================================
class DepartamentoImportItem(BaseModel):
    codigo_iso: str = Field(..., min_length=2, max_length=2)
    nombre: str = Field(..., min_length=1, max_length=100)


class MunicipioImportItem(BaseModel):
    codigo_iso: str = Field(..., min_length=4, max_length=4)
    nombre: str = Field(..., min_length=1, max_length=100)
    departamento_codigo: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Código ISO del departamento padre",
    )


class GeografiaImportResult(BaseModel):
    """Resultado de importación"""
    departamentos_creados: int = 0
    departamentos_actualizados: int = 0
    municipios_creados: int = 0
    municipios_actualizados: int = 0
    omitidos: int = 0
    errores: list[str] = []


# ============================================================
# VISTA COMBINADA
# ============================================================
class DepartamentoConMunicipiosResponse(DepartamentoResponse):
    """Departamento con sus municipios anidados"""
    municipios: list[MunicipioListResponse] = []