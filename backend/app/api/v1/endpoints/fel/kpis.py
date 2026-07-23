"""
Endpoints para KPIs de Facturas Electrónicas (FEL).
"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.dependencies.empresa import get_active_empresa
from app.models.tenant_models import Empresa
from app.schemas.fel.kpis import KPIsResponse
from app.services.fel.kpis_service import FELKPIsService

logger = logging.getLogger(__name__)
router = APIRouter()


async def _set_schema_for_query(
    db: AsyncSession,
    scope: DataScope,
    tenant_id: int | None = None,
) -> str:
    """Configura el search_path correcto según el rol del usuario."""
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id},
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": scope.tenant_id},
        )
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")
    schema_name = row[0]
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name


@router.get("/kpis", response_model=KPIsResponse)
async def get_fel_kpis(
    empresa_id: int | None = Query(None, description="ID de la empresa"),
    fecha_inicio: date = Query(
        default_factory=lambda: date.today().replace(day=1),
        description="Fecha de inicio del período (YYYY-MM-DD)"
    ),
    fecha_fin: date = Query(
        default_factory=date.today,
        description="Fecha de fin del período (YYYY-MM-DD)"
    ),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    """
    Obtiene los KPIs de facturas electrónicas para un período.
    
    Incluye:
    - Compras, Ventas Locales y Exportaciones (sin IVA)
    - Crédito Fiscal y Débito Fiscal
    - IVA por pagar (Débito - Crédito)
    - Conteos de documentos (Emitidos, Recibidos, Anulados)
    - Series temporales por mes para gráficos
    """
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            400,
            detail="La fecha de inicio debe ser anterior a la fecha de fin"
        )
    
    # Limitar rango máximo a 5 años para evitar consultas pesadas
    dias_maximos = 365 * 5
    if (fecha_fin - fecha_inicio).days > dias_maximos:
        raise HTTPException(
            400,
            detail=f"El rango máximo permitido es de {dias_maximos} días"
        )
    
    # Configurar schema del tenant
    await _set_schema_for_query(db, scope, tenant_id)
    
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    if not empresa_id_final:
        raise HTTPException(400, detail="Debe especificar una empresa")
    
    # Obtener nombre de la empresa
    emp_res = await db.execute(
        text("SELECT nombre FROM empresas WHERE id = :eid"),
        {"eid": empresa_id_final},
    )
    empresa_row = emp_res.first()
    empresa_nombre = empresa_row[0] if empresa_row else None
    
    return await FELKPIsService.get_kpis(
        db=db,
        empresa_id=empresa_id_final,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        empresa_nombre=empresa_nombre,
    )