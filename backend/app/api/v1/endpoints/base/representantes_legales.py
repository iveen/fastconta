# app/api/v1/endpoints/representantes_legales.py
"""Endpoints para gestión de Representantes Legales por Empresa"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.models.tenant_models import Empresa
from app.schemas.base.representante_legal import (
    RepresentanteLegalCreate,
    RepresentanteLegalOut,
    RepresentanteLegalUpdate,
)
from app.services.base.representante_legal_service import RepresentanteLegalService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/empresas/{empresa_id}/representantes",
    tags=["Representantes Legales"],
)


# ============================================================
# HELPERS
# ============================================================
async def _resolver_schema(
    db: AsyncSession,
    scope: DataScope,
    tenant_id: int | None = None,  # ✅ BIGINT (era str)
) -> str:
    """Resuelve el schema_name a usar según el rol del usuario."""
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id}  # ✅ int (no str)
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": scope.tenant_id}  # ✅ int (no str)
        )
    
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")
    
    schema_name = row[0]
    if not schema_name.strip().replace("_", "").isalnum():
        raise HTTPException(500, detail="Esquema con formato inválido")
    
    return schema_name


async def _verificar_empresa(
    db: AsyncSession, schema_name: str, empresa_id: int  # ✅ BIGINT
) -> None:
    """Verifica que la empresa exista en el schema del tenant."""
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")


def get_service(db: AsyncSession = Depends(get_public_db)) -> RepresentanteLegalService:
    return RepresentanteLegalService(db)


# ============================================================
# 1. Listar representantes de una empresa
# ============================================================
@router.get("/", response_model=list[RepresentanteLegalOut])
async def listar_representantes(
    empresa_id: int,  # ✅ BIGINT (era UUID)
    solo_activos: bool = Query(True, description="Solo mostrar representantes activos"),
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: RepresentanteLegalService = Depends(get_service),
):
    """Lista todos los representantes legales de una empresa"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    representantes = await service.obtener_representantes_por_empresa(
        empresa_id, solo_activos=solo_activos
    )
    return [RepresentanteLegalOut.model_validate(r) for r in representantes]


# ============================================================
# 2. Crear representante
# ============================================================
@router.post("/", response_model=RepresentanteLegalOut, status_code=status.HTTP_201_CREATED)
async def crear_representante(
    empresa_id: int,  # ✅ BIGINT
    payload: RepresentanteLegalCreate,
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: RepresentanteLegalService = Depends(get_service),
):
    """Crea un nuevo representante legal para una empresa"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    await _verificar_empresa(db, schema_name, empresa_id)
    
    # ✅ Validar que no exista duplicado
    es_duplicado = await service.verificar_duplicado(
        empresa_id=empresa_id,
        tipo_identificacion=payload.tipo_identificacion,
        numero_identificacion=payload.numero_identificacion,
    )
    if es_duplicado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un representante legal con {payload.tipo_identificacion} '{payload.numero_identificacion}' en esta empresa."
        )
    
    data = payload.model_dump()
    data["empresa_id"] = empresa_id
    representante = await service.crear_representante(data)
    return RepresentanteLegalOut.model_validate(representante)


# ============================================================
# 3. Actualizar representante
# ============================================================
@router.put("/{representante_id}", response_model=RepresentanteLegalOut)
async def actualizar_representante(
    empresa_id: int,  # ✅ BIGINT
    representante_id: int,  # ✅ BIGINT (era UUID)
    payload: RepresentanteLegalUpdate,
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: RepresentanteLegalService = Depends(get_service),
):
    """Actualiza un representante legal existente"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    # Si cambia el identificador, validar que no sea duplicado
    update_data = payload.model_dump(exclude_unset=True)
    if "tipo_identificacion" in update_data or "numero_identificacion" in update_data:
        tipo_id = update_data.get("tipo_identificacion")
        numero_id = update_data.get("numero_identificacion")
        
        # Obtener valores actuales si no están en el payload
        representante_actual = await service.obtener_representante_por_id(representante_id, empresa_id)
        if representante_actual is None:
            raise HTTPException(status_code=404, detail="Representante legal no encontrado")
        
        tipo_id = tipo_id or representante_actual.tipo_identificacion
        numero_id = numero_id or representante_actual.numero_identificacion
        
        es_duplicado = await service.verificar_duplicado(
            empresa_id=empresa_id,
            tipo_identificacion=tipo_id,
            numero_identificacion=numero_id,
            representante_id_excluir=representante_id,
        )
        if es_duplicado:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe otro representante legal con {tipo_id} '{numero_id}' en esta empresa."
            )
    
    representante = await service.actualizar_representante(representante_id, empresa_id, update_data)
    if representante is None:
        raise HTTPException(status_code=404, detail="Representante legal no encontrado")
    
    return RepresentanteLegalOut.model_validate(representante)


# ============================================================
# 4. Eliminar representante (soft delete)
# ============================================================
@router.delete("/{representante_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_representante(
    empresa_id: int,  # ✅ BIGINT
    representante_id: int,  # ✅ BIGINT
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: RepresentanteLegalService = Depends(get_service),
):
    """Elimina un representante legal (soft delete)"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    eliminado = await service.eliminar_representante(representante_id, empresa_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Representante legal no encontrado")
    
    return None