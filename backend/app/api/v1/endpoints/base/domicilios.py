# app/api/v1/endpoints/domicilios.py
"""Endpoints para gestión de Domicilios por Empresa"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.schemas.base.domicilio import (
    DomicilioCreate,
    DomicilioOut,
    DomicilioUpdate,
)
from app.services.base.domicilio_service import DomicilioService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/empresas/{empresa_id}/domicilios",
    tags=["Domicilios"],
)


# ============================================================
# HELPERS
# ============================================================
async def _resolver_schema(
    db: AsyncSession,
    scope: DataScope,
    tenant_id: int | None = None,  # ✅ BIGINT
) -> str:
    """Resuelve el schema_name a usar según el rol del usuario."""
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id}
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": scope.tenant_id}
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
    from app.models.tenant_models import Empresa
    
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")


def get_service(db: AsyncSession = Depends(get_public_db)) -> DomicilioService:
    return DomicilioService(db)


# ============================================================
# LISTAR domicilios
# ============================================================
@router.get("/", response_model=list[DomicilioOut])
async def listar_domicilios(
    empresa_id: int,  # ✅ BIGINT (era UUID)
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: DomicilioService = Depends(get_service),
):
    """Lista todos los domicilios de una empresa"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    domicilios = await service.obtener_domicilios_por_empresa(empresa_id)
    return [DomicilioOut(**DomicilioService.enriquecer_domicilio(d)) for d in domicilios]


# ============================================================
# CREAR domicilio
# ============================================================
@router.post("/", response_model=DomicilioOut, status_code=status.HTTP_201_CREATED)
async def crear_domicilio(
    empresa_id: int,  # ✅ BIGINT
    payload: DomicilioCreate,
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: DomicilioService = Depends(get_service),
):
    """Crea un nuevo domicilio para una empresa"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    await _verificar_empresa(db, schema_name, empresa_id)
    
    data = payload.model_dump()
    data["empresa_id"] = empresa_id
    domicilio = await service.crear_domicilio(data)
    return DomicilioOut(**DomicilioService.enriquecer_domicilio(domicilio))


# ============================================================
# ACTUALIZAR domicilio
# ============================================================
@router.put("/{domicilio_id}", response_model=DomicilioOut)
async def actualizar_domicilio(
    empresa_id: int,  # ✅ BIGINT
    domicilio_id: int,  # ✅ BIGINT (era UUID)
    payload: DomicilioUpdate,
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: DomicilioService = Depends(get_service),
):
    """Actualiza un domicilio existente"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    data = payload.model_dump(exclude_unset=True)
    domicilio = await service.actualizar_domicilio(domicilio_id, empresa_id, data)
    
    if domicilio is None:
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")
    
    return DomicilioOut(**DomicilioService.enriquecer_domicilio(domicilio))


# ============================================================
# ELIMINAR domicilio
# ============================================================
@router.delete("/{domicilio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_domicilio(
    empresa_id: int,  # ✅ BIGINT
    domicilio_id: int,  # ✅ BIGINT
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    service: DomicilioService = Depends(get_service),
):
    """Elimina un domicilio"""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    eliminado = await service.eliminar_domicilio(domicilio_id, empresa_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")
    
    return None