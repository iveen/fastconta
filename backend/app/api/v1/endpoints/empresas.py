# app/api/v1/endpoints/empresas.py
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db, get_tenant_db
from app.dependencies import require_role
from app.models.global_models import Tenant
from app.models.tenant_models import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaOut, EmpresaUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


# ==========================================
# 0. NUEVO: Listar empresas activas (para dropdown de contexto)
# ==========================================
@router.get("/mis-empresas", response_model=list[EmpresaOut])
async def get_mis_empresas(
    db: AsyncSession = Depends(get_tenant_db)
):
    """
    Endpoint específico para el dropdown de contexto de empresa.
    Retorna solo las empresas activas del tenant del usuario.
    Versión simplificada para evitar timeouts.
    """
    # ✅ Query simple y directa
    result = await db.execute(
        select(Empresa)
        .where(Empresa.is_active.is_(True))
        .order_by(Empresa.nombre)
        .limit(100)  # ✅ Limitar resultados para performance
    )
    empresas = result.scalars().all()
    
    return [EmpresaOut.model_validate(e) for e in empresas]


# ==========================================
# 1. Listar todas las empresas (con filtro para superadmin)
# ==========================================
@router.get("/", response_model=list[EmpresaOut])
async def list_empresas(
    tenant_id: str | None = Query(None, description="ID del tenant a consultar (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    schema_name = None
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id para listar empresas")
        
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

    if not schema_name.strip().replace("_", "").isalnum():
        raise HTTPException(500, detail="Esquema con formato inválido")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    result = await db.execute(select(Empresa).order_by(Empresa.nombre))
    empresas = result.scalars().all()

    return [EmpresaOut.model_validate(e) for e in empresas]


# ==========================================
# 2. Crear empresa
# ==========================================
@router.post("/", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED)
async def create_empresa(
    payload: EmpresaCreate,
    db: AsyncSession = Depends(get_tenant_db),
    _: dict = Depends(require_role("admin", "superadmin"))
):
    tenant_id = db.info["current_user"]["tenant_id"]
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one()
    
    count_result = await db.execute(select(func.count(Empresa.id)))
    empresas_count = count_result.scalar()

    if tenant.plan == "freemium" and empresas_count >= tenant.max_empresas:
        raise HTTPException(
            status_code=403,
            detail=f"Límite de empresas alcanzado ({tenant.max_empresas}) en plan freemium."
        )

    empresa = Empresa(
        nombre=payload.nombre,
        nit=payload.nit,
        direccion=payload.direccion,
    )
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)

    return EmpresaOut.model_validate(empresa)


# ==========================================
# 3. Obtener empresa por ID
# ==========================================
@router.get("/{empresa_id}", response_model=EmpresaOut)
async def get_empresa(
    empresa_id: str,
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    schema_name = None
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id}
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": str(scope.tenant_id)}
        )
    
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")

    schema_name = row[0]

    if not schema_name.strip().replace("_", "").isalnum():
        raise HTTPException(500, detail="Esquema con formato inválido")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    return EmpresaOut.model_validate(empresa)


# ==========================================
# 4. Actualizar empresa
# ==========================================
@router.put("/{empresa_id}", response_model=EmpresaOut)
async def update_empresa(
    empresa_id: str,
    payload: EmpresaUpdate,
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    schema_name = None
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id}
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": str(scope.tenant_id)}
        )
    
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")

    schema_name = row[0]

    if not schema_name.strip().replace("_", "").isalnum():
        raise HTTPException(500, detail="Esquema con formato inválido")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(empresa, field, value)

    await db.commit()
    await db.refresh(empresa)

    return EmpresaOut.model_validate(empresa)