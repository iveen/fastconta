# app/api/v1/endpoints/superadmin.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_superadmin
from app.db.session import get_public_db
from app.schemas.tenant import TenantCreate, TenantResponse
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/superadmin/tenants", tags=["Superadmin"])


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_public_db),
    current_user: dict = Depends(get_current_superadmin),
):
    """Lista tenants desde public.tenants, SIN consultar tablas de tenant."""
    result = await db.execute(
        text("""
            SELECT id, name, nit, schema_name, plan, max_empresas, is_active, created_at
            FROM public.tenants
            WHERE is_active = true
            ORDER BY created_at DESC
            OFFSET :skip LIMIT :limit
        """),
        {"skip": skip, "limit": limit}
    )
    return [dict(row) for row in result.mappings().all()]


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_public_db),
    current_user: dict = Depends(get_current_superadmin)
):
    """Crea un nuevo tenant (lógica completa en TenantService)."""
    service = TenantService(db)
    try:
        result = await service.create_tenant(
            tenant_name=payload.tenant_name,
            nit=payload.nit,
            admin_email=payload.admin_email,
            admin_password=payload.admin_password,
            plan=payload.plan
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.patch("/{tenant_id}/status")
async def toggle_status(
    tenant_id: str,
    is_active: bool,
    db: AsyncSession = Depends(get_public_db),
    current_user: dict = Depends(get_current_superadmin)
):
    """Activa o suspende un tenant."""
    await db.execute(
        text("UPDATE public.tenants SET is_active = :active WHERE id = :id"),
        {"active": is_active, "id": tenant_id}
    )
    await db.commit()
    return {"message": "Estado actualizado", "is_active": is_active}