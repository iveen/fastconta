# app/api/v1/endpoints/periodos_fiscales.py
from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db, get_tenant_db
from app.models.tenant_models import Empresa, PeriodoFiscal

router = APIRouter()

# ==========================================
# Esquemas
# ==========================================
class PeriodoFiscalCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    empresa_id: UUID

class PeriodoFiscalOut(BaseModel):
    id: UUID
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    cerrado: bool
    empresa_id: UUID

    class Config:
        from_attributes = True

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
# 1. Listar períodos (con filtro para superadmin)
# ==========================================
@router.get("/", response_model=List[PeriodoFiscalOut])
async def listar_periodos(
    empresa_id: UUID | None = Query(None, description="Filtrar por empresa"),
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    stmt = select(PeriodoFiscal).order_by(PeriodoFiscal.fecha_inicio.desc())
    if empresa_id:
        stmt = stmt.where(PeriodoFiscal.empresa_id == empresa_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# ==========================================
# 2. Crear período (usa get_tenant_db para usuarios normales)
# ==========================================
@router.post("/", response_model=PeriodoFiscalOut, status_code=status.HTTP_201_CREATED)
async def crear_periodo(
    payload: PeriodoFiscalCreate,
    db: AsyncSession = Depends(get_tenant_db)
):
    # Validar que la empresa existe
    result_emp = await db.execute(select(Empresa).where(Empresa.id == payload.empresa_id))
    if not result_emp.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Empresa no encontrada")
    
    # Validar que no exista otro período con el mismo nombre y empresa
    existente = await db.execute(
        select(PeriodoFiscal).where(
            PeriodoFiscal.nombre == payload.nombre,
            PeriodoFiscal.empresa_id == payload.empresa_id
        )
    )
    if existente.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un período con ese nombre para la empresa")

    periodo = PeriodoFiscal(**payload.dict())
    db.add(periodo)
    await db.commit()
    await db.refresh(periodo)
    return periodo