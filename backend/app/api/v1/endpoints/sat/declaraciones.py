"""Endpoint para Declaraciones SAT"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.fel.facturas import _set_schema_for_query
from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.schemas.sat.declaracion import (
    AjusteManualRequest,
    DeclaracionSombraOut,
    GenerarSombraRequest,
)
from app.services.sat.declaraciones_service import (
    aplicar_ajuste_manual,
    finalizar_declaracion,
    generar_formulario_sombra,
    obtener_declaracion,
    obtener_facturas_casilla,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/declaraciones", tags=["Declaraciones SAT"])


# ============================================================
# 1. GENERAR / RECALCULAR FORMULARIO SOMBRA
# ============================================================
@router.post("/sombra", status_code=status.HTTP_200_OK)
async def generar_sombra(
    request: GenerarSombraRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Genera o regenera la declaración sombra del SAT-2237"""
    await _set_schema_for_query(db, scope)
    try:
        resultado = await generar_formulario_sombra(
            db=db,
            empresa_id=request.empresa_id,
            anio=request.anio,
            mes=request.mes,
            codigo_formulario=request.codigo_formulario,
            usuario_id=scope.user.id if scope.user else None,
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al generar sombra: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================
# 2. OBTENER DETALLE DE UNA DECLARACIÓN
# ============================================================
@router.get("/{declaracion_id}", response_model=DeclaracionSombraOut)
async def obtener_decl(
    declaracion_id: int,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Obtiene una declaración con todos sus detalles"""
    await _set_schema_for_query(db, scope)
    resultado = await obtener_declaracion(db, declaracion_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
    return DeclaracionSombraOut(**resultado)


# ============================================================
# 3. APLICAR AJUSTE MANUAL
# ============================================================
@router.patch("/{declaracion_id}/casillas/{casilla_codigo}/ajuste", status_code=status.HTTP_200_OK)
async def aplicar_ajuste(
    declaracion_id: int,
    casilla_codigo: str,
    request: AjusteManualRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Aplica un ajuste manual a una casilla y recalcula totales"""
    await _set_schema_for_query(db, scope)
    try:
        resultado = await aplicar_ajuste_manual(
            db=db,
            declaracion_id=declaracion_id,
            casilla_codigo=casilla_codigo,
            base_imponible=request.base_imponible,
            monto_impuesto=request.monto_impuesto,
            motivo_ajuste=request.motivo_ajuste,
            usuario_id=scope.user.id if scope.user else None,
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 4. FINALIZAR DECLARACIÓN
# ============================================================
@router.post("/{declaracion_id}/finalizar", status_code=status.HTTP_200_OK)
async def finalizar(
    declaracion_id: int,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Finaliza una declaración (ya no se puede modificar)"""
    await _set_schema_for_query(db, scope)
    try:
        resultado = await finalizar_declaracion(
            db=db,
            declaracion_id=declaracion_id,
            usuario_id=scope.user.id if scope.user else None,
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 5. DRILL-DOWN: Ver facturas de una casilla
# ============================================================
@router.get("/{declaracion_id}/casillas/{casilla_codigo}/facturas")
async def obtener_facturas(
    declaracion_id: int,
    casilla_codigo: str,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Obtiene las facturas asociadas a una casilla de la declaración"""
    await _set_schema_for_query(db, scope)
    facturas = await obtener_facturas_casilla(db, declaracion_id, casilla_codigo)
    return {"casilla_codigo": casilla_codigo, "facturas": facturas}
