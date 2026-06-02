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
from app.schemas.empresa import EmpresaCreate, EmpresaOut

logger = logging.getLogger(__name__)
router = APIRouter()

# ==========================================
# 1. Listar empresas (con filtro para superadmin)
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
        
        # Obtener schema del tenant solicitado
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": tenant_id}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]
    else:
        # Comportamiento normal: usar el schema del token del usuario
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": str(scope.tenant_id)}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]

    # 🔒 Validar formato de schema para prevenir inyección SQL
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")

    # Cambiar search_path temporalmente para esta transacción
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    result = await db.execute(select(Empresa).order_by(Empresa.nombre))
    empresas = result.scalars().all()
    
    return [EmpresaOut.model_validate(e) for e in empresas]

# ==========================================
# 2. Crear empresa (solo para usuarios de tenant)
# ==========================================
@router.post("/", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED)
async def create_empresa(
    payload: EmpresaCreate,
    db: AsyncSession = Depends(get_tenant_db),
    _: dict = Depends(require_role("admin", "superadmin"))
):
    # 1. Obtener tenant_id desde el token (almacenado por get_tenant_db)
    tenant_id = db.info["current_user"]["tenant_id"]
    
    # 2. Obtener plan del tenant
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one()

    # 3. Contar empresas actuales del tenant
    count_result = await db.execute(select(func.count(Empresa.id)))
    empresas_count = count_result.scalar()

    # 4. Validar límite freemium
    if tenant.plan == "freemium" and empresas_count >= tenant.max_empresas:
        raise HTTPException(
            status_code=403,
            detail=f"Límite de empresas alcanzado ({tenant.max_empresas}) en plan freemium."
        )

    # 5. Crear empresa
    empresa = Empresa(
        nombre=payload.nombre,
        nit=payload.nit,
        direccion=payload.direccion,
    )
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)

    return EmpresaOut.model_validate(empresa)