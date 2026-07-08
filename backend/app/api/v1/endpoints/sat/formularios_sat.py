# app/api/v1/endpoints/formularios_sat.py
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.global_models import FormularioSat, SeccionFormulario
from app.schemas.sat.formulario import (
    FormularioSatCreate,
    FormularioSatDetail,
    FormularioSatDuplicarRequest,
    FormularioSatHistorial,
    FormularioSatResponse,
    FormularioSatUpdate,
)
from app.services.sat.formulario_service import FormularioSatService

router = APIRouter(prefix="/formularios-sat", tags=["Configuración Fiscal - Formularios"])
logger = logging.getLogger(__name__)


def get_service(db: AsyncSession = Depends(get_db)) -> FormularioSatService:
    return FormularioSatService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_formularios(
    codigo: str | None = Query(None),
    es_version_activa: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: FormularioSatService = Depends(get_service),
):
    # 1️ Subconsulta eficiente para contar secciones
    subquery_sec = select(func.count(SeccionFormulario.id)).where(
        SeccionFormulario.formulario_id == FormularioSat.id
    ).correlate(FormularioSat).scalar_subquery()

    # 2️⃣ Query principal con el conteo como columna virtual
    query = select(FormularioSat, subquery_sec.label("total_secciones"))
    if codigo:
        query = query.where(FormularioSat.codigo == codigo)
    if es_version_activa is not None:
        query = query.where(FormularioSat.es_version_activa.is_(es_version_activa))

    # Contar total para paginación
    count_query = select(func.count()).select_from(query.subquery())
    total = (await service.db.execute(count_query)).scalar() or 0

    # Paginar y ejecutar
    query = query.order_by(FormularioSat.codigo, FormularioSat.version.desc())
    query = query.offset(skip).limit(limit)
    result = await service.db.execute(query)
    rows = result.all()

    # 3️⃣ Mapear a formato JSON esperado por el frontend
    data = []
    for form, total_sec in rows:
        form_dict = {
            "id": form.id,  # ✅ int (era str(form.id))
            "codigo": form.codigo,
            "version": form.version,
            "nombre": form.nombre,
            "descripcion": form.descripcion,
            "fecha_vigencia_desde": form.fecha_vigencia_desde.isoformat() if form.fecha_vigencia_desde else None,
            "fecha_vigencia_hasta": form.fecha_vigencia_hasta.isoformat() if form.fecha_vigencia_hasta else None,
            "es_version_activa": form.es_version_activa,
            "formulario_padre_id": form.formulario_padre_id,  # ✅ int (era str)
            "total_secciones": total_sec or 0,
        }
        data.append(form_dict)
    return {"data": data, "total": total, "skip": skip, "limit": limit}


# ============================================================
# HISTORIAL DE VERSIONES
# ============================================================
@router.get("/{codigo}/historial", response_model=FormularioSatHistorial)
async def obtener_historial(
    codigo: str,
    service: FormularioSatService = Depends(get_service),
):
    """Obtiene el historial completo de versiones de un formulario"""
    historial = await service.obtener_historial(codigo)
    if not historial["versiones"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe formulario con código {codigo}",
        )
    return historial


# ============================================================
# VERSIÓN VIGENTE
# ============================================================
@router.get("/{codigo}/vigente", response_model=FormularioSatDetail)
async def obtener_vigente(
    codigo: str,
    fecha: Optional[date] = Query(None, description="Fecha de vigencia (default: hoy)"),
    service: FormularioSatService = Depends(get_service),
):
    """Obtiene la versión vigente de un formulario para una fecha específica"""
    formulario = await service.obtener_vigente(codigo, fecha)
    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe versión vigente de {codigo} para la fecha {fecha or date.today()}",
        )
    return formulario


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/id/{formulario_id}", response_model=FormularioSatDetail)
async def obtener_por_id(
    formulario_id: int,  # ✅ BIGINT (era UUID)
    service: FormularioSatService = Depends(get_service),
):
    """Obtiene un formulario con todas sus secciones y casillas"""
    formulario = await service.obtener_por_id(formulario_id)
    if formulario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulario no encontrado"
        )
    return formulario


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=FormularioSatResponse, status_code=status.HTTP_201_CREATED)
async def crear_formulario(
    data: FormularioSatCreate,
    service: FormularioSatService = Depends(get_service),
):
    """Crea un nuevo formulario SAT"""
    formulario = await service.crear(data.model_dump())
    return formulario


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{formulario_id}", response_model=FormularioSatResponse)
async def actualizar_formulario(
    formulario_id: int,  # ✅ BIGINT (era UUID)
    data: FormularioSatUpdate,
    service: FormularioSatService = Depends(get_service),
):
    """Actualiza un formulario existente"""
    formulario = await service.actualizar(formulario_id, data.model_dump(exclude_unset=True))
    if not formulario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulario no encontrado",
        )
    return formulario


# ============================================================
# DUPLICAR VERSIÓN
# ============================================================
@router.post("/{formulario_id}/duplicar", response_model=FormularioSatDetail)
async def duplicar_version(
    formulario_id: int,  # ✅ BIGINT (era UUID)
    data: FormularioSatDuplicarRequest,
    service: FormularioSatService = Depends(get_service),
):
    """
    Duplica un formulario creando una nueva versión.
    Permite copiar secciones, casillas, reglas y exclusiones.
    """
    try:
        nuevo = await service.duplicar_version(
            formulario_id=formulario_id,
            nueva_version=data.nueva_version,
            fecha_vigencia_desde=data.fecha_vigencia_desde,
            copiar_casillas=data.copiar_casillas,
            copiar_secciones=data.copiar_secciones,
            copiar_reglas=data.copiar_reglas_filtrado,
            copiar_exclusiones=data.copiar_exclusiones,
        )
        return nuevo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================
# ELIMINAR (soft delete)
# ============================================================
@router.delete("/{formulario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_formulario(
    formulario_id: int,  # ✅ BIGINT (era UUID)
    service: FormularioSatService = Depends(get_service),
):
    """Desactiva un formulario (soft delete)"""
    eliminado = await service.eliminar(formulario_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulario no encontrado",
        )