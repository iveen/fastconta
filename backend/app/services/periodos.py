# app/services/periodos.py
from datetime import date
from uuid import UUID

from app.models.tenant_models import PeriodoFiscal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def validar_periodo_abierto_por_fecha(
    db: AsyncSession, 
    empresa_id: UUID, 
    fecha: date
) -> PeriodoFiscal:
    """
    Valida que exista un período fiscal para la fecha dada y que NO esté cerrado.
    Retorna el objeto PeriodoFiscal si es válido.
    Ideal para: Creación/Edición de Partidas, Facturas, Depreciaciones, etc.
    """
    stmt = select(PeriodoFiscal).where(
        PeriodoFiscal.empresa_id == empresa_id,
        PeriodoFiscal.fecha_inicio <= fecha,
        PeriodoFiscal.fecha_fin >= fecha
    )
    periodo = (await db.execute(stmt)).scalar_one_or_none()
    
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No existe un período fiscal definido para la fecha {fecha}."
        )
    
    if periodo.cerrado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"⛔ Operación denegada: El período fiscal '{periodo.nombre}' ya está cerrado. No se permiten modificaciones."
        )
    
    return periodo


async def validar_periodo_abierto_por_id(
    db: AsyncSession, 
    periodo_id: UUID,
    empresa_id: UUID
) -> PeriodoFiscal:
    """
    Valida que un período específico exista, pertenezca a la empresa y NO esté cerrado.
    Ideal para: Procesos masivos como el Cierre Anual o Depreciación Mensual.
    """
    periodo = await db.get(PeriodoFiscal, periodo_id)
    
    if not periodo or periodo.empresa_id != empresa_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período fiscal no encontrado o no pertenece a la empresa."
        )
        
    if periodo.cerrado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"⛔ Operación denegada: El período fiscal '{periodo.nombre}' ya está cerrado."
        )
        
    return periodo