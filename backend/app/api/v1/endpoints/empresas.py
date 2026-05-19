from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_tenant_db
from app.schemas.empresa import EmpresaCreate, EmpresaOut
from sqlalchemy import text

router = APIRouter()

@router.get("/", response_model=list[EmpresaOut])
async def list_empresas(db: AsyncSession = Depends(get_tenant_db)):
    result = await db.execute(text("SELECT id, nombre, nit, direccion, created_at FROM empresas"))
    rows = result.fetchall()
    return [{"id": row[0], "nombre": row[1], "nit": row[2], "direccion": row[3], "created_at": row[4]} for row in rows]

@router.post("/", response_model=EmpresaOut, status_code=status.HTTP_201_CREATED)
async def create_empresa(payload: EmpresaCreate, db: AsyncSession = Depends(get_tenant_db)):
    query = text("INSERT INTO empresas (nombre, nit, direccion) VALUES (:nombre, :nit, :direccion) RETURNING id, nombre, nit, direccion, created_at")
    result = await db.execute(query, {"nombre": payload.nombre, "nit": payload.nit, "direccion": payload.direccion})
    row = result.fetchone()
    await db.commit()
    return {"id": row[0], "nombre": row[1], "nit": row[2], "direccion": row[3], "created_at": row[4]}