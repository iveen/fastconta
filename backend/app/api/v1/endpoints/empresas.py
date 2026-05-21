from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_tenant_db
from app.models.tenant_models import Empresa
from app.models.global_models import Tenant
from app.schemas.empresa import EmpresaCreate, EmpresaOut
from app.dependencies import require_role

router = APIRouter()

@router.get("/", response_model=list[EmpresaOut])
async def list_empresas(db: AsyncSession = Depends(get_tenant_db)):
    result = await db.execute(select(Empresa).order_by(Empresa.nombre))
    empresas = result.scalars().all()
    return [EmpresaOut.model_validate(e) for e in empresas]

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