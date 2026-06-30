# app/api/v1/endpoints/sat_libros.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.core.tenant_utils import set_tenant_search_path
from app.db.session import get_public_db
from app.dependencies.empresa import get_active_empresa  # ✅ NUEVO
from app.models.global_models import TipoLibro
from app.models.tenant_models import Empresa  # ✅ NUEVO
from app.schemas.sat_libros import (
    SatLibroCreate,
    SatLibroDetailResponse,
    SatLibroResponse,
)
from app.services.sat_libros_service import (
    finalizar_libro_sat,
    obtener_libro_detallado,
    procesar_y_generar_libro_sat,
)

router = APIRouter()


# ==========================================
# 1. Generar Libro IVA
# ==========================================
@router.post("/generar", response_model=SatLibroResponse, status_code=status.HTTP_201_CREATED)
async def generar_libro_iva(
    payload: SatLibroCreate,
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)  # ✅ NUEVO (opcional)
):
    await set_tenant_search_path(db, scope, tenant_id)
    
    # ✅ Sobrescribir empresa_id del payload con el del header si existe
    if empresa_from_header:
        payload.empresa_id = empresa_from_header.id
    
    if not payload.empresa_id:
        raise HTTPException(
            status_code=400,
            detail="Debe especificar una empresa (header X-Company-Id o en el payload)"
        )
    
    return await procesar_y_generar_libro_sat(db=db, payload=payload)


# ==========================================
# 2. Consultar Libro IVA
# ==========================================
@router.get("/consultar", response_model=SatLibroDetailResponse)
async def consultar_libro_iva(
    empresa_id: UUID | None = Query(None, description="ID de la empresa (opcional, usa X-Company-Id)"),  # ✅ Cambiado a opcional
    tipo_libro: str = Query(..., description="Tipo de libro: 'compras' o 'ventas'"),
    anio: int = Query(..., ge=2020, le=2100),
    mes: int = Query(..., ge=1, le=12),
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)  # ✅ NUEVO
):
    await set_tenant_search_path(db, scope, tenant_id)
    
    # ✅ Usar empresa_id del header si no se pasó como query param
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    
    if not empresa_id_final:
        raise HTTPException(
            status_code=400,
            detail="Debe especificar una empresa (query param o header X-Company-Id)"
        )
    
    # 1. Resolver el código del tipo de libro a su UUID
    query_tipo = select(TipoLibro).where(TipoLibro.codigo == tipo_libro.lower())
    result = await db.execute(query_tipo)
    tipo_libro_obj = result.scalar_one_or_none()

    if not tipo_libro_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El tipo de libro '{tipo_libro}' no existe. Valores válidos: 'compras', 'ventas'."
        )

    libro = await obtener_libro_detallado(
        db=db, 
        empresa_id=empresa_id_final,  # ✅ Usar empresa_id_final
        tipo_libro=tipo_libro_obj, 
        anio=anio, 
        mes=mes
    )

    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró ningún registro ni borrador generado para este periodo. Por favor, genérelo primero."
        )
        
    return libro


# ==========================================
# 3. Finalizar Libro IVA
# ==========================================
@router.patch("/{libro_id}/finalizar", response_model=SatLibroResponse)
async def cerrar_libro_iva(
    libro_id: UUID,
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await set_tenant_search_path(db, scope, tenant_id)
    user_info = db.info.get("current_user") or {}
    usuario_id = user_info.get("sub")
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Usuario no autenticado en la sesión.")

    return await finalizar_libro_sat(db=db, libro_id=libro_id, usuario_id=usuario_id)