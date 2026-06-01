

from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_tenant_db
from app.models.tenant_models import Empresa, PeriodoFiscal

router = APIRouter()

# ---------- Esquemas ----------
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

# ---------- Endpoints ----------
@router.get("/", response_model=List[PeriodoFiscalOut])
async def listar_periodos(
    empresa_id: UUID | None = Query(None, description="Filtrar por empresa"),
    db: AsyncSession = Depends(get_tenant_db)
):
    stmt = select(PeriodoFiscal).order_by(PeriodoFiscal.fecha_inicio.desc())
    if empresa_id:
        stmt = stmt.where(PeriodoFiscal.empresa_id == empresa_id)
    result = await db.execute(stmt)
    return result.scalars().all()

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