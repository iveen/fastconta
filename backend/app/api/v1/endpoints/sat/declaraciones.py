# app/api/v1/endpoints/declaraciones.py
import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.fel.facturas import _set_schema_for_query
from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.models.global_models import CasillaSat, FormularioSat
from app.models.tenant_models import (
    DeclaracionImpuesto,
    DeclaracionImpuestoFactura,
    DetalleDeclaracionImpuesto,
    FacturaElectronica,
)
from app.schemas.sat.declaracion import (
    AjusteManualRequest,
    CasillaDetalleOut,
    DeclaracionSombraOut,
    GenerarSombraRequest,
)
from app.services.sat.declaraciones_service import generar_formulario_sombra

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/declaraciones", tags=["Declaraciones SAT"])


# ============================================================
# 1. GENERAR / RECALCULAR FORMULARIO SOMBRA
# ============================================================
@router.post("/sombra", status_code=status.HTTP_200_OK)
async def generar_sombra(
    request: GenerarSombraRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope)
    try:
        resultado = await generar_formulario_sombra(
            db=db,
            empresa_id=request.empresa_id,  # ✅ Ya es int en el schema
            anio=request.anio,
            mes=request.mes,
            codigo_formulario=request.codigo_formulario
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al generar sombra: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al procesar la declaración: {str(e)}")


# ============================================================
# 2. OBTENER DETALLE DE UNA DECLARACIÓN
# ============================================================
@router.get("/{declaracion_id}", response_model=DeclaracionSombraOut)
async def obtener_declaracion(
    declaracion_id: int,  # ✅ BIGINT (era UUID)
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope)
    stmt = (
        select(DeclaracionImpuesto, FormularioSat.codigo)
        .join(FormularioSat, DeclaracionImpuesto.formulario_sat_id == FormularioSat.id)
        .options(selectinload(DeclaracionImpuesto.detalles).selectinload(DetalleDeclaracionImpuesto.casilla))
        .where(DeclaracionImpuesto.id == declaracion_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
    declaracion, formulario_codigo = row
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


# ============================================================
# 3. APLICAR AJUSTE MANUAL A UNA CASILLA
# ============================================================
@router.patch("/{declaracion_id}/casillas/{casilla_codigo}/ajuste", status_code=status.HTTP_200_OK)
async def aplicar_ajuste_manual(
    declaracion_id: int,  # ✅ BIGINT (era UUID)
    casilla_codigo: str,
    request: AjusteManualRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope)
    stmt_decl = select(DeclaracionImpuesto).where(DeclaracionImpuesto.id == declaracion_id)
    res_decl = await db.execute(stmt_decl)
    declaracion = res_decl.scalar_one_or_none()
    if not declaracion:
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
    if declaracion.estado == "FINALIZADO":
        raise HTTPException(status_code=400, detail="No se puede modificar una declaración finalizada")

    stmt_casilla = select(CasillaSat.id).join(FormularioSat).where(
        FormularioSat.id == declaracion.formulario_sat_id,
        CasillaSat.codigo == casilla_codigo
    )
    res_casilla = await db.execute(stmt_casilla)
    casilla_id = res_casilla.scalar_one_or_none()
    if not casilla_id:
        raise HTTPException(status_code=404, detail=f"Casilla {casilla_codigo} no pertenece a este formulario")

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
            ajustado_por=scope.user.id  # ✅ CORREGIDO: scope.user.id (no scope.user_id)
        )
        .returning(DetalleDeclaracionImpuesto.id)
    )
    res_update = await db.execute(stmt_update)
    if not res_update.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Detalle de casilla no encontrado")

    # RECÁLCULO DE TOTALES
    # ⚠️ CasillaSat no tiene campo 'tipo_valor'. Usamos 'naturaleza' como alternativa.
    # Mapeo: DEBITO → naturaleza='deudora', CREDITO → naturaleza='acreedora'
    stmt_detalles = select(DetalleDeclaracionImpuesto, CasillaSat.naturaleza).join(
        CasillaSat, DetalleDeclaracionImpuesto.casilla_sat_id == CasillaSat.id
    ).where(DetalleDeclaracionImpuesto.declaracion_id == declaracion_id)
    res_detalles = await db.execute(stmt_detalles)
    total_debito = Decimal("0.00")
    total_credito = Decimal("0.00")
    for det, naturaleza in res_detalles.all():
        # ✅ CORREGIDO: Usar naturaleza en lugar de tipo_valor
        if naturaleza == "deudora":  # Mapeado a DEBITO
            total_debito += det.monto_impuesto
        elif naturaleza == "acreedora":  # Mapeado a CREDITO
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


# ============================================================
# 4. FINALIZAR DECLARACIÓN
# ============================================================
@router.post("/{declaracion_id}/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_declaracion(
    declaracion_id: int,  # ✅ BIGINT (era UUID)
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope)
    stmt = (
        update(DeclaracionImpuesto)
        .where(DeclaracionImpuesto.id == declaracion_id)
        .values(
            estado="FINALIZADO",
            fecha_cierre=func.now(),
            finalizado_por=scope.user.id  # ✅ CORREGIDO: scope.user.id (no scope.user_id)
        )
        .returning(DeclaracionImpuesto.id)
    )
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Declaración no encontrada")
    await db.commit()
    return {"mensaje": "Declaración finalizada y bloqueada exitosamente"}


# ============================================================
# 5. DRILL-DOWN: Ver facturas que componen una casilla
# ============================================================
@router.get("/{declaracion_id}/casillas/{casilla_codigo}/facturas")
async def obtener_facturas_de_casilla(
    declaracion_id: int,  # ✅ BIGINT (era UUID)
    casilla_codigo: str,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope)
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

    stmt_facturas = (
        select(FacturaElectronica, DeclaracionImpuestoFactura.base_asignada, DeclaracionImpuestoFactura.impuesto_asignado)
        .join(DeclaracionImpuestoFactura, FacturaElectronica.id == DeclaracionImpuestoFactura.factura_id)
        .where(DeclaracionImpuestoFactura.detalle_declaracion_id == detalle_id)
    )
    res_facturas = await db.execute(stmt_facturas)
    facturas_out = []
    for factura, base_asig, imp_asig in res_facturas.all():
        facturas_out.append({
            "factura_id": factura.id,  # ✅ CORREGIDO: int (no str)
            "numero": f"{factura.serie}-{factura.numero}",
            "fecha_emision": factura.fecha_emision.strftime("%Y-%m-%d") if factura.fecha_emision else None,
            "tercero": factura.receptor_nombre if factura.tipo_operacion == 'Venta' else factura.emisor_nombre,
            "nit": factura.receptor_nit if factura.tipo_operacion == 'Venta' else factura.emisor_nit,
            "base_asignada": float(base_asig),
            "impuesto_asignado": float(imp_asig)
        })
    return {"casilla_codigo": casilla_codigo, "facturas": facturas_out}