# app/api/v1/endpoints/plan_cuentas.py
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.dependencies.empresa import get_active_empresa
from app.models.tenant_models import CuentaContable, Empresa
from app.schemas.contabilidad.plan_cuentas import CuentaCreate, CuentaOut, CuentaUpdate
from app.services.contabilidad.plan_cuentas_service import (
    exportar_plan_cuentas,
    procesar_importacion_excel,
)

router = APIRouter()


# ============================================================
# Helper: Configurar search_path según rol
# ============================================================
async def _set_schema_for_query(
    db: AsyncSession, 
    scope: DataScope, 
    tenant_id: int | None = None  # ✅ BIGINT (era str)
) -> str:
    """Configura el search_path correcto según el rol del usuario."""
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
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")
    
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name


# ============================================================
# Helper: Obtener el schema actual
# ============================================================
async def _get_current_schema(db: AsyncSession) -> str:
    """Obtiene el schema_name actual configurado en la sesión."""
    result = await db.execute(text("SELECT current_schema()"))
    schema = result.scalar()
    return schema or "public"


# ============================================================
# 1. Listar cuentas
# ============================================================
@router.get("/", response_model=List[CuentaOut])
async def list_cuentas(
    empresa_id: int | None = Query(None, description="Filtrar por empresa (BIGINT)"),  # ✅ BIGINT
    tenant_id: int | None = Query(None, description="ID del tenant (requerido para superadmin)"),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    
    stmt = select(CuentaContable).order_by(CuentaContable.codigo)
    if empresa_id_final:
        stmt = stmt.where(
            and_(
                CuentaContable.empresa_id == empresa_id_final,
                CuentaContable.is_active.is_(True)  # ✅ CORREGIDO: is_active en lugar de activa
            )
        )
    
    result = await db.execute(stmt)
    return result.scalars().all()


# ============================================================
# 2. Crear cuenta
# ============================================================
@router.post("/", response_model=CuentaOut, status_code=201)
async def create_cuenta(
    cuenta: CuentaCreate,
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    schema_name = await _get_current_schema(db)
    
    # Validar que no exista el código
    check_sql = text(f"""
        SELECT id FROM {schema_name}.plan_cuentas 
        WHERE codigo = :codigo AND empresa_id = :empresa_id AND is_active = true
    """)
    result = await db.execute(check_sql, {
        "codigo": cuenta.codigo, 
        "empresa_id": cuenta.empresa_id  # ✅ int (no str)
    })
    
    if result.first():
        raise HTTPException(
            status_code=400, 
            detail=f"El código {cuenta.codigo} ya existe en esta empresa."
        )
    
    # ✅ CORREGIDO: INSERT sin ID, usar RETURNING para obtener el ID generado
    insert_sql = text(f"""
        INSERT INTO {schema_name}.plan_cuentas 
        (codigo, nombre, tipo, naturaleza, acepta_tercero, nivel, cuenta_padre_id, empresa_id, is_active, created_at)
        VALUES 
        (:codigo, :nombre, :tipo, :naturaleza, :acepta_tercero, :nivel, :cuenta_padre_id, :empresa_id, true, NOW())
        RETURNING id, codigo, nombre, tipo, naturaleza, acepta_tercero, nivel, cuenta_padre_id, is_active, created_at
    """)
    
    result = await db.execute(insert_sql, {
        "codigo": cuenta.codigo,
        "nombre": cuenta.nombre,
        "tipo": cuenta.tipo,
        "naturaleza": cuenta.naturaleza,
        "acepta_tercero": cuenta.acepta_tercero,
        "nivel": cuenta.nivel,
        "cuenta_padre_id": cuenta.cuenta_padre_id,  # ✅ int (no str)
        "empresa_id": cuenta.empresa_id  # ✅ int (no str)
    })
    
    row = result.first()
    await db.commit()
    
    # ✅ CORREGIDO: Construir respuesta desde RETURNING
    return CuentaOut(
        id=row[0],
        codigo=row[1],
        nombre=row[2],
        tipo=row[3],
        naturaleza=row[4],
        acepta_tercero=row[5],
        nivel=row[6],
        cuenta_padre_id=row[7],
        is_active=row[8],  # ✅ Renombrado
        created_at=row[9]
    )


# ============================================================
# 3. Importar Excel
# ============================================================
@router.post("/importar")
async def importar_plan_cuentas(
    file: UploadFile = File(...),
    empresa_id: int = Form(..., description="ID de la empresa (BIGINT, Obligatorio)"),  # ✅ BIGINT
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    schema_name = await _get_current_schema(db)
    
    # ✅ CORREGIDO: is_active en lugar de activa
    check_sql = text(f"""
        SELECT 1 FROM {schema_name}.plan_cuentas 
        WHERE empresa_id = :empresa_id AND is_active = true 
        LIMIT 1
    """)
    exists = await db.execute(check_sql, {"empresa_id": empresa_id})  # ✅ int (no str)
    
    if exists.scalar():
        raise HTTPException(
            status_code=400,
            detail="⚠️ Importación bloqueada: Esta empresa ya tiene un Plan de Cuentas configurado."
        )
    
    return await procesar_importacion_excel(file, empresa_id, db, schema_name)


# ============================================================
# 4. Exportar a Excel
# ============================================================
@router.get("/exportar")
async def exportar_plan_cuentas_endpoint(
    empresa_id: int = Query(..., description="ID de la empresa (BIGINT)"),  # ✅ BIGINT
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    schema_name = await _get_current_schema(db)
    
    excel_buffer = await exportar_plan_cuentas(empresa_id, db, schema_name)
    
    return StreamingResponse(
        iter([excel_buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=plan_cuentas_{empresa_id}.xlsx"}
    )


# ============================================================
# 5. Obtener cuenta por ID
# ============================================================
@router.get("/{cuenta_id}", response_model=CuentaOut)
async def get_cuenta(
    cuenta_id: int,  # ✅ BIGINT (era str)
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    result = await db.execute(
        select(CuentaContable).where(CuentaContable.id == cuenta_id)
    )
    cuenta = result.scalar_one_or_none()
    
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    return cuenta


# ============================================================
# 6. Actualizar cuenta
# ============================================================
@router.put("/{cuenta_id}", response_model=CuentaOut)
async def update_cuenta(
    cuenta_id: int,  # ✅ BIGINT (era UUID)
    cuenta_data: CuentaUpdate,
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    schema_name = await _get_current_schema(db)
    
    # Construir dinámicamente el UPDATE solo con los campos enviados
    update_fields = []
    params = {"id": cuenta_id}  # ✅ int (no str)
    data = cuenta_data.model_dump(exclude_unset=True)
    
    for key, value in data.items():
        update_fields.append(f"{key} = :{key}")
        params[key] = value  # ✅ Sin str() conversion
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar.")
    
    sql = text(f"""
        UPDATE {schema_name}.plan_cuentas 
        SET {', '.join(update_fields)} 
        WHERE id = :id 
        RETURNING id, codigo, nombre, tipo, naturaleza, acepta_tercero, nivel, cuenta_padre_id, is_active, created_at
    """)
    
    result = await db.execute(sql, params)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    await db.commit()
    
    return CuentaOut(
        id=row[0], 
        codigo=row[1], 
        nombre=row[2], 
        tipo=row[3], 
        naturaleza=row[4],
        acepta_tercero=row[5], 
        nivel=row[6], 
        cuenta_padre_id=row[7], 
        is_active=row[8],  # ✅ Renombrado
        created_at=row[9]
    )


# ============================================================
# 7. Eliminar cuenta (Soft Delete)
# ============================================================
@router.delete("/{cuenta_id}", status_code=204)
async def delete_cuenta(
    cuenta_id: int,  # ✅ BIGINT (era UUID)
    tenant_id: int | None = Query(None),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    schema_name = await _get_current_schema(db)
    
    # ✅ CORREGIDO: is_active en lugar de activa
    sql = text(f"""
        UPDATE {schema_name}.plan_cuentas 
        SET is_active = false 
        WHERE id = :id 
        RETURNING id
    """)
    
    result = await db.execute(sql, {"id": cuenta_id})  # ✅ int (no str)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    await db.commit()
    return None