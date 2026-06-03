# app/api/v1/endpoints/sat_libros.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.models.global_models import TipoLibro
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
# Helper: Configurar search_path según rol
# ==========================================
async def _set_schema_for_query(db: AsyncSession, scope: DataScope, tenant_id: str | None = None):
    """Configura el search_path correcto según el rol del usuario."""
    schema_name = None
    
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": tenant_id}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": str(scope.tenant_id)}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]

    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name

# ==========================================
# 1. Generar Libro IVA
# ==========================================
@router.post("/generar", response_model=SatLibroResponse, status_code=status.HTTP_201_CREATED)
async def generar_libro_iva(
    payload: SatLibroCreate,
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    return await procesar_y_generar_libro_sat(db=db, payload=payload)

# ==========================================
# 2. Consultar Libro IVA
# ==========================================
@router.get("/consultar", response_model=SatLibroDetailResponse)
async def consultar_libro_iva(
    empresa_id: UUID = Query(...),
    tipo_libro: str = Query(..., description="Tipo de libro: 'compras' o 'ventas'"),
    anio: int = Query(..., ge=2020, le=2100),
    mes: int = Query(..., ge=1, le=12),
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)

        # 1. Resolver el código del tipo de libro a su UUID
    # Asumimos que en tu tabla TipoLibro tienes registros con codigo='compras' y codigo='ventas'
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
        empresa_id=empresa_id, 
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
    await _set_schema_for_query(db, scope, tenant_id)
    
    user_info = db.info.get("current_user") or {}
    usuario_id = user_info.get("sub")
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Usuario no autenticado en la sesión.")

    return await finalizar_libro_sat(db=db, libro_id=libro_id, usuario_id=usuario_id)