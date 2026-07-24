# app/api/v1/endpoints/empresas.py
"""Endpoints para gestión de Empresas"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db, get_tenant_db
from app.dependencies import require_role
from app.models.tenant_models import Empresa
from app.schemas.base.empresa import (
    EmpresaCreate,
    EmpresaOut,
    EmpresaSimple,
    EmpresaUpdate,
    NitValidarRequest,
)
from app.services.facturas.validacion_service import validar_nit_guatemala

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# HELPER: Resolver esquema del tenant
# ============================================================
async def _resolver_schema(
    db: AsyncSession,
    scope: DataScope,
    tenant_id: int | None = None  # ✅ BIGINT (era str)
) -> str:
    """Resuelve el schema_name a usar según el rol del usuario."""
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
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


# ============================================================
# HELPER: Validar NIT (formato + unicidad)
# ============================================================
async def _validar_nit(
    db: AsyncSession,
    schema_name: str,
    nit: str,
    empresa_id_excluir: int | None = None  # ✅ BIGINT (era str)
) -> None:
    """Valida el formato del NIT y su unicidad dentro del tenant."""
    if not validar_nit_guatemala(nit):
        raise HTTPException(
            status_code=400,
            detail=f"El NIT '{nit}' no es válido según las reglas de la SAT de Guatemala."
        )
    
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    query = select(Empresa).where(Empresa.nit == nit)
    if empresa_id_excluir:
        query = query.where(Empresa.id != empresa_id_excluir)
    
    result = await db.execute(query)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una empresa con el NIT '{nit}' en esta firma."
        )


# ============================================================
# 0. Listar empresas activas (dropdown de contexto)
# ============================================================
@router.get("/mis-empresas", response_model=list[EmpresaSimple])
async def get_mis_empresas(
    db: AsyncSession = Depends(get_tenant_db)
):
    """Endpoint para el dropdown de contexto de empresa."""
    try:
        result = await db.execute(
            select(Empresa)
            .where(Empresa.is_active.is_(True))
            .order_by(Empresa.nombre)
            .limit(100)
        )
        empresas = result.scalars().all()
        return [EmpresaSimple.model_validate(e) for e in empresas]
    except Exception as e:
        logger.exception(f"Error en get_mis_empresas: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al cargar empresas: {e!s}"
        )


# ============================================================
# 1. Listar todas las empresas
# ============================================================
@router.get("/", response_model=list[EmpresaOut])
async def list_empresas(
    tenant_id: int | None = Query(None, description="ID del tenant (requerido para superadmin)"),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    result = await db.execute(select(Empresa).order_by(Empresa.nombre))
    empresas = result.scalars().all()
    return [EmpresaOut.model_validate(e) for e in empresas]


# ============================================================
# 2. Crear empresa (SIN validación de max_empresas)
# ============================================================
@router.post("/", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED)
async def create_empresa(
    payload: EmpresaCreate,
    scope: DataScope = Depends(get_data_scope),
    tenant_id: int | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    db: AsyncSession = Depends(get_public_db),
    _: dict = Depends(require_role("tenant_manager", "superadmin"))
):
    """Crea una nueva empresa en el schema del tenant."""
    
    # 1. Resolver el tenant_id objetivo
    target_tenant_id = tenant_id if scope.role_code == "superadmin" else scope.tenant_id
    
    # 2. Obtener el schema_name del tenant desde la BD pública
    res = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
        {"tid": target_tenant_id}
    )
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")
    schema_name = row[0]
    
    # 3. Configurar search_path para esta transacción
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    # 4. Validar NIT (formato + unicidad)
    await _validar_nit(db, schema_name, payload.nit)
    
    # 5. Crear la instancia de la empresa
    empresa = Empresa(
        tenant_id=target_tenant_id,  # ✅ CRUCIAL: Asignar el tenant_id explícitamente
        nombre=payload.nombre,
        nit=payload.nit,
        razon_social=payload.razon_social,
        nombre_comercial=payload.nombre_comercial,
        fecha_constitucion=payload.fecha_constitucion,
        regimen_fiscal_id=payload.regimen_fiscal_id,
        tipo_persona_id=payload.tipo_persona_id,
        actividad_economica_id=payload.actividad_economica_id,
        direccion=payload.direccion,
    )
    db.add(empresa)
    
    try:
        # ✅ PASO A: Flush envía el INSERT a la BD y obtiene el ID y defaults del servidor
        await db.flush()
        
        # ✅ PASO B: Refresh recarga el objeto dentro de la MISMA transacción 
        # (el search_path AÚN es válido aquí)
        await db.refresh(empresa)
        
        # ✅ PASO C: Commit cierra la transacción (ya no importa que se pierda el search_path)
        await db.commit()
        
    except IntegrityError:
        await db.rollback()
        logger.error(f"IntegrityError al crear empresa: NIT duplicado '{payload.nit}'")
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una empresa con el NIT '{payload.nit}'."
        )
        
    return EmpresaOut.model_validate(empresa)

# ============================================================
# 3. Obtener empresa por ID
# ============================================================
@router.get("/{empresa_id}", response_model=EmpresaOut)
async def get_empresa(
    empresa_id: int,  # ✅ BIGINT (era str)
    tenant_id: int | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    result = await db.execute(
        select(Empresa)
        .options(
            selectinload(Empresa.regimen_fiscal),
            selectinload(Empresa.tipo_persona),
            selectinload(Empresa.actividad_economica)
        )
        .where(Empresa.id == empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return EmpresaOut.model_validate(empresa)


# ============================================================
# 4. Actualizar empresa (CON VALIDACIÓN DE NIT)
# ============================================================
@router.put("/{empresa_id}", response_model=EmpresaOut)
async def update_empresa(
    empresa_id: int,  # ✅ BIGINT (era str)
    payload: EmpresaUpdate,
    tenant_id: int | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    _: dict = Depends(require_role("tenant_manager", "superadmin")) 
):
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Si el NIT cambió, validarlo
    update_data = payload.model_dump(exclude_unset=True)
    if "nit" in update_data and update_data["nit"] != empresa.nit:
        await _validar_nit(db, schema_name, update_data["nit"], empresa_id_excluir=empresa_id)
    
    for field, value in update_data.items():
        setattr(empresa, field, value)
    
    try:
        await db.commit()
        await db.refresh(empresa)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe otra empresa con el NIT '{update_data.get('nit')}'."
        )
    
    return EmpresaOut.model_validate(empresa)


# ============================================================
# 5. Desactivar empresa (Soft Delete)
# ============================================================
@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_empresa(
    empresa_id: int,  # ✅ BIGINT (era str)
    tenant_id: int | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    _: dict = Depends(require_role("tenant_manager", "superadmin")) 
):
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    empresa.is_active = False
    await db.commit()


# ============================================================
# 6. Validar NIT
# ============================================================
@router.post("/validar-nit", status_code=status.HTTP_200_OK)
async def validar_nit_endpoint(
    payload: NitValidarRequest,
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """Valida formato y unicidad del NIT sin crear la empresa."""
    schema_name = await _resolver_schema(db, scope, tenant_id)
    await _validar_nit(db, schema_name, payload.nit)
    return {"valido": True, "nit": payload.nit}