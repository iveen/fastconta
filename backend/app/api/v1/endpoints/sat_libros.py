# app/api/v1/endpoints/sat_libros.py
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID

from app.db.session import get_tenant_db
from app.models.tenant_models import TipoLibro
from app.schemas.sat_libros import SatLibroCreate, SatLibroResponse, SatLibroDetailResponse
from app.services.sat_libros_service import (
    procesar_y_generar_libro_sat, 
    obtener_libro_detallado,
    finalizar_libro_sat
)


router = APIRouter()

@router.post("/generar", response_model=SatLibroResponse, status_code=status.HTTP_201_CREATED)
async def generar_libro_iva(
    payload: SatLibroCreate, 
    db: AsyncSession = Depends(get_tenant_db)
):
    """
    Calcula, limpia (idempotencia) y puebla el libro de IVA desde las facturas FEL.
    """
    user_info = db.info.get("current_user")
    
    schema_name = user_info.get("schema") or user_info.get("tenant_schema")
    if not schema_name and user_info.get("tenant_id"):
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": user_info["tenant_id"]}
        )
        row = res.fetchone()
        schema_name = row[0] if row else None

    if not schema_name:
        raise HTTPException(400, "Schema no determinado")

    # Establecer la ruta de búsqueda de PostgreSQL para el Tenant actual
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    return await procesar_y_generar_libro_sat(db=db, payload=payload)


@router.get("/consultar", response_model=SatLibroDetailResponse)
async def consultar_libro_iva(
    empresa_id: UUID = Query(...),
    tipo_libro: TipoLibro = Query(...),
    anio: int = Query(..., ge=2020, le=2100),
    mes: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_tenant_db)
):
    """
    Retorna la cabecera y el array completo de líneas ('lineas': [...])
    para un mes y año específicos dentro del Tenant.
    """
    libro = await obtener_libro_detallado(
        db=db, 
        empresa_id=empresa_id, 
        tipo_libro=tipo_libro, 
        anio=anio, 
        mes=mes
    )
    
    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró ningún registro ni borrador generado para este periodo. Por favor, genérelo primero."
        )
        
    return libro


@router.patch("/{libro_id}/finalizar", response_model=SatLibroResponse)
async def cerrar_libro_iva(
    libro_id: UUID,
    db: AsyncSession = Depends(get_tenant_db), # 👈 Única dependencia necesaria
):
    """
    Congela el libro pasándolo a estado 'finalizado'. Bloquea recálculos futuros.
    """
    # 🕵️‍♂️ Extraemos el ID del usuario contador directamente de la sesión tal como en tu arquitectura
    user_info = db.info.get("current_user") or {}
    usuario_id = user_info.get("sub") # O el campo donde guardes el ID (ej: "id", "user_id")
    
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Usuario no autenticado en la sesión.")

    return await finalizar_libro_sat(db=db, libro_id=libro_id, usuario_id=usuario_id)