import logging
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Importamos el helper de search_path desde el módulo de facturas
from app.api.v1.endpoints.facturas import _set_schema_for_query
from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.models.global_models import CasillaSat, FormularioSat
from app.models.tenant_models import (
    DeclaracionImpuesto,
    DeclaracionImpuestoFactura,
    DetalleDeclaracionImpuesto,
    FacturaElectronica,
)
from app.schemas.declaracion import (
    AjusteManualRequest,
    CasillaDetalleOut,
    DeclaracionSombraOut,
    GenerarSombraRequest,
)
from app.services.declaraciones_service import generar_formulario_sombra

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/declaraciones", tags=["Declaraciones SAT"])


# ==============================================================================
# 1. GENERAR / RECALCULAR FORMULARIO SOMBRA
# ==============================================================================
@router.post("/sombra", status_code=status.HTTP_200_OK)
async def generar_sombra(
    request: GenerarSombraRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """
    Genera o recalcula el formulario sombra. 
    Respeta los ajustes manuales previos (no los sobrescribe).
    """
    # Configurar search_path para el tenant
    await _set_schema_for_query(db, scope)
    
    try:
        resultado = await generar_formulario_sombra(
            db=db,
            empresa_id=request.empresa_id,
            anio=request.anio,
            mes=request.mes,
            codigo_formulario=request.codigo_formulario
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error al generar sombra: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error interno al procesar la declaración: {str(e)}")


# ==============================================================================
# 2. OBTENER DETALLE DE UNA DECLARACIÓN (Con Drill-down de casillas)
# ==============================================================================
@router.get("/{declaracion_id}", response_model=DeclaracionSombraOut)
async def obtener_declaracion(
    declaracion_id: UUID,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope)

    # Consulta uniendo con el catálogo global para obtener nombres de casillas
    stmt = (
        select(DeclaracionImpuesto, FormularioSat.codigo)
        .join(FormularioSat, DeclaracionImpuesto.formulario_sat_id == FormularioSat.id)
        .options(
            selectinload(DeclaracionImpuesto.detalles).selectinload(DetalleDeclaracionImpuesto.casilla)
        )
        .where(DeclaracionImpuesto.id == declaracion_id)
    )
    
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
        
    declaracion, formulario_codigo = row
    
    # Mapeo manual para cumplir con el schema Pydantic anidado
    detalles_out = [
        CasillaDetalleOut(
            casilla_codigo=det.casilla.codigo,
            casilla_nombre=det.casilla.nombre,
            seccion=det.casilla.seccion,
            tipo_casilla=det.casilla.tipo_casilla,
            base_imponible=det.base_imponible,
            monto_impuesto=det.monto_impuesto,
            es_ajuste_manual=det.es_ajuste_manual,
            motivo_ajuste=det.motivo_ajuste
        )
        for det in declaracion.detalles
    ]
    
    return DeclaracionSombraOut(
        id=declaracion.id,
        empresa_id=declaracion.empresa_id,
        formulario_codigo=formulario_codigo,
        anio=declaracion.anio,
        mes=declaracion.mes,
        estado=declaracion.estado,
        total_debito_fiscal=declaracion.total_debito_fiscal,
        total_credito_fiscal=declaracion.total_credito_fiscal,
        impuesto_a_pagar=declaracion.impuesto_a_pagar,
        remanente_siguiente_periodo=declaracion.remanente_siguiente_periodo,
        detalles=detalles_out,
        created_at=declaracion.created_at
    )


# ==============================================================================
# 3. APLICAR AJUSTE MANUAL A UNA CASILLA (Con Auditoría)
# ==============================================================================
@router.patch("/{declaracion_id}/casillas/{casilla_codigo}/ajuste", status_code=status.HTTP_200_OK)
async def aplicar_ajuste_manual(
    declaracion_id: UUID,
    casilla_codigo: str,
    request: AjusteManualRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """
    Permite al contador sobrescribir un valor calculado automáticamente.
    Requiere un motivo y marca la casilla como 'ajuste manual' para protegerla 
    de futuros recalculos automáticos.
    """
    await _set_schema_for_query(db, scope)

    # 1. Verificar que la declaración existe y no está finalizada
    stmt_decl = select(DeclaracionImpuesto).where(DeclaracionImpuesto.id == declaracion_id)
    res_decl = await db.execute(stmt_decl)
    declaracion = res_decl.scalar_one_or_none()
    
    if not declaracion:
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
    if declaracion.estado == "FINALIZADO":
        raise HTTPException(status_code=400, detail="No se puede modificar una declaración finalizada")

    # 2. Buscar la casilla específica en el catálogo global
    stmt_casilla = select(CasillaSat.id).join(FormularioSat).where(
        FormularioSat.id == declaracion.formulario_sat_id,
        CasillaSat.codigo == casilla_codigo
    )
    res_casilla = await db.execute(stmt_casilla)
    casilla_id = res_casilla.scalar_one_or_none()
    
    if not casilla_id:
        raise HTTPException(status_code=404, detail=f"Casilla {casilla_codigo} no pertenece a este formulario")

    # 3. Actualizar el detalle
    stmt_update = (
        update(DetalleDeclaracionImpuesto)
        .where(
            DetalleDeclaracionImpuesto.declaracion_id == declaracion_id,
            DetalleDeclaracionImpuesto.casilla_sat_id == casilla_id
        )
        .values(
            base_imponible=request.base_imponible if request.base_imponible is not None else DetalleDeclaracionImpuesto.base_imponible,
            monto_impuesto=request.monto_impuesto if request.monto_impuesto is not None else DetalleDeclaracionImpuesto.monto_impuesto,
            es_ajuste_manual=True,
            motivo_ajuste=request.motivo_ajuste,
            ajustado_por=scope.user_id
        )
        .returning(DetalleDeclaracionImpuesto.id)
    )
    
    res_update = await db.execute(stmt_update)
    if not res_update.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Detalle de casilla no encontrado")

    # 4. RECÁLCULO DE TOTALES
    stmt_detalles = select(DetalleDeclaracionImpuesto, CasillaSat.tipo_valor).join(
        CasillaSat, DetalleDeclaracionImpuesto.casilla_sat_id == CasillaSat.id
    ).where(DetalleDeclaracionImpuesto.declaracion_id == declaracion_id)
    
    res_detalles = await db.execute(stmt_detalles)
    
    total_debito = Decimal("0.00")
    total_credito = Decimal("0.00")
    
    for det, tipo_valor in res_detalles.all():
        if tipo_valor == "DEBITO":
            total_debito += det.monto_impuesto
        elif tipo_valor == "CREDITO":
            total_credito += det.monto_impuesto

    impuesto_determinado = total_debito - total_credito
    
    await db.execute(
        update(DeclaracionImpuesto)
        .where(DeclaracionImpuesto.id == declaracion_id)
        .values(
            total_debito_fiscal=total_debito,
            total_credito_fiscal=total_credito,
            impuesto_determinado=impuesto_determinado,
            impuesto_a_pagar=max(Decimal("0.00"), impuesto_determinado)
        )
    )
    
    await db.commit()
    return {"mensaje": "Ajuste manual aplicado y totales recalculados exitosamente"}


# ==============================================================================
# 4. FINALIZAR DECLARACIÓN (Bloqueo)
# ==============================================================================
@router.post("/{declaracion_id}/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_declaracion(
    declaracion_id: UUID,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """
    Bloquea la declaración. Cambia el estado a FINALIZADO y registra 
    quién y cuándo lo hizo. Esto evita sobrescrituras accidentales.
    """
    await _set_schema_for_query(db, scope)

    stmt = (
        update(DeclaracionImpuesto)
        .where(DeclaracionImpuesto.id == declaracion_id)
        .values(
            estado="FINALIZADO",
            fecha_cierre=func.now(),
            finalizado_por=scope.user_id
        )
        .returning(DeclaracionImpuesto.id)
    )
    
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
        
    await db.commit()
    return {"mensaje": "Declaración finalizada y bloqueada exitosamente"}


# ==============================================================================
# 5. DRILL-DOWN: Ver facturas que componen una casilla
# ==============================================================================
@router.get("/{declaracion_id}/casillas/{casilla_codigo}/facturas")
async def obtener_facturas_de_casilla(
    declaracion_id: UUID,
    casilla_codigo: str,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """
    Devuelve la lista de facturas que suman el monto de una casilla específica.
    Es la funcionalidad "Drill-down" que da confianza al contador.
    """
    await _set_schema_for_query(db, scope)

    # 1. Obtener el ID del detalle de la casilla
    stmt = (
        select(DetalleDeclaracionImpuesto.id)
        .join(CasillaSat, DetalleDeclaracionImpuesto.casilla_sat_id == CasillaSat.id)
        .join(DeclaracionImpuesto, DetalleDeclaracionImpuesto.declaracion_id == DeclaracionImpuesto.id)
        .where(
            DeclaracionImpuesto.id == declaracion_id,
            CasillaSat.codigo == casilla_codigo
        )
    )
    res = await db.execute(stmt)
    detalle_id = res.scalar_one_or_none()
    
    if not detalle_id:
        raise HTTPException(status_code=404, detail="Casilla no encontrada en esta declaración")

    # 2. Obtener las facturas asociadas
    stmt_facturas = (
        select(FacturaElectronica, DeclaracionImpuestoFactura.base_asignada, DeclaracionImpuestoFactura.impuesto_asignado)
        .join(DeclaracionImpuestoFactura, FacturaElectronica.id == DeclaracionImpuestoFactura.factura_id)
        .where(DeclaracionImpuestoFactura.detalle_declaracion_id == detalle_id)
    )
    
    res_facturas = await db.execute(stmt_facturas)
    
    facturas_out = []
    for factura, base_asig, imp_asig in res_facturas.all():
        facturas_out.append({
            "factura_id": str(factura.id),
            "numero": f"{factura.serie}-{factura.numero}",
            "fecha_emision": factura.fecha_emision.strftime("%Y-%m-%d") if factura.fecha_emision else None,
            "tercero": factura.receptor_nombre if factura.tipo_operacion == 'Venta' else factura.emisor_nombre,
            "nit": factura.receptor_nit if factura.tipo_operacion == 'Venta' else factura.emisor_nit,
            "base_asignada": float(base_asig),
            "impuesto_asignado": float(imp_asig)
        })
        
    return {"casilla_codigo": casilla_codigo, "facturas": facturas_out}