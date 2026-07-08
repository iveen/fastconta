"""Endpoint para Geografía (Departamentos y Municipios)"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.catalogos.geografia import (
    DepartamentoCreate,
    DepartamentoResponse,
    DepartamentoUpdate,
    MunicipioCreate,
    MunicipioResponse,
    MunicipioUpdate,
)
from app.services.catalogos.geografia_service import GeografiaService

router = APIRouter(prefix="/geografia", tags=["Catálogos - Geografía"])


def get_service(db: AsyncSession = Depends(get_db)) -> GeografiaService:
    return GeografiaService(db)


# ============================================================
# DEPARTAMENTOS
# ============================================================
@router.get("/departamentos", response_model=list[DepartamentoResponse])
async def listar_departamentos(
    service: GeografiaService = Depends(get_service),
):
    """Lista todos los departamentos"""
    return await service.obtener_departamentos()


@router.get("/departamentos/{depto_id}", response_model=DepartamentoResponse)
async def obtener_departamento(
    depto_id: int,  # ✅ BIGINT (era UUID)
    service: GeografiaService = Depends(get_service),
):
    """Obtiene un departamento por ID"""
    depto = await service.obtener_departamento_por_id(depto_id)
    if not depto:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")
    return depto


@router.post("/departamentos", response_model=DepartamentoResponse, status_code=201)
async def crear_departamento(
    data: DepartamentoCreate,
    service: GeografiaService = Depends(get_service),
):
    """Crea un nuevo departamento"""
    try:
        return await service.crear_departamento(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/departamentos/{depto_id}", response_model=DepartamentoResponse)
async def actualizar_departamento(
    depto_id: int,  # ✅ BIGINT (era UUID)
    data: DepartamentoUpdate,
    service: GeografiaService = Depends(get_service),
):
    """Actualiza un departamento"""
    depto = await service.actualizar_departamento(depto_id, data.model_dump(exclude_unset=True))
    if not depto:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")
    return depto


@router.delete("/departamentos/{depto_id}", status_code=204)
async def eliminar_departamento(
    depto_id: int,  # ✅ BIGINT (era UUID)
    service: GeografiaService = Depends(get_service),
):
    """Elimina un departamento (soft delete)"""
    if not await service.eliminar_departamento(depto_id):
        raise HTTPException(status_code=404, detail="Departamento no encontrado")


# ============================================================
# MUNICIPIOS
# ============================================================
@router.get("/municipios", response_model=list[MunicipioResponse])
async def listar_municipios(
    departamento_id: int | None = Query(None, description="Filtrar por departamento"),
    service: GeografiaService = Depends(get_service),
):
    """Lista municipios, opcionalmente filtrados por departamento"""
    municipios = await service.obtener_municipios(departamento_id)
    
    # Enriquecer con nombre del departamento
    response = []
    for m in municipios:
        data = MunicipioResponse.model_validate(m).model_dump()
        data["departamento_nombre"] = m.departamento.nombre if m.departamento else None
        response.append(data)
    return response


@router.get("/municipios/{mun_id}", response_model=MunicipioResponse)
async def obtener_municipio(
    mun_id: int,  # ✅ BIGINT (era UUID)
    service: GeografiaService = Depends(get_service),
):
    """Obtiene un municipio por ID"""
    mun = await service.obtener_municipio_por_id(mun_id)
    if not mun:
        raise HTTPException(status_code=404, detail="Municipio no encontrado")
    
    data = MunicipioResponse.model_validate(mun).model_dump()
    data["departamento_nombre"] = mun.departamento.nombre if mun.departamento else None
    return data


@router.post("/municipios", response_model=MunicipioResponse, status_code=201)
async def crear_municipio(
    data: MunicipioCreate,
    service: GeografiaService = Depends(get_service),
):
    """Crea un nuevo municipio"""
    try:
        return await service.crear_municipio(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/municipios/{mun_id}", response_model=MunicipioResponse)
async def actualizar_municipio(
    mun_id: int,  # ✅ BIGINT (era UUID)
    data: MunicipioUpdate,
    service: GeografiaService = Depends(get_service),
):
    """Actualiza un municipio"""
    mun = await service.actualizar_municipio(mun_id, data.model_dump(exclude_unset=True))
    if not mun:
        raise HTTPException(status_code=404, detail="Municipio no encontrado")
    return mun


@router.delete("/municipios/{mun_id}", status_code=204)
async def eliminar_municipio(
    mun_id: int,  # ✅ BIGINT (era UUID)
    service: GeografiaService = Depends(get_service),
):
    """Elimina un municipio (soft delete)"""
    if not await service.eliminar_municipio(mun_id):
        raise HTTPException(status_code=404, detail="Municipio no encontrado")