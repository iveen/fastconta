# app/services/cierre_contable.py
from decimal import Decimal

from app.crud.secuencias import get_next_poliza
from app.models.tenant_models import (
    CuentaContable,
    DetallePartida,
    Empresa,
    Partida,
    PeriodoFiscal,
)
from fastapi import HTTPException, status
from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def ejecutar_cierre_anual(
    db: AsyncSession,
    empresa_id: int,  # ✅ BIGINT
    periodo_id: int,  # ✅ BIGINT
) -> dict:
    try:
        # =========================================================================
        # 0. VALIDACIONES INICIALES
        # =========================================================================
        empresa = await db.get(Empresa, empresa_id)
        if not empresa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
        if not empresa.cuenta_utilidad_periodo_id or not empresa.cuenta_utilidades_acumuladas_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La empresa no tiene configuradas las cuentas de 'Utilidad del Período' y 'Utilidades Acumuladas'."
            )
        periodo = await db.get(PeriodoFiscal, periodo_id)
        if not periodo or periodo.empresa_id != empresa_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período fiscal no encontrado o no pertenece a la empresa")
        if periodo.cerrado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El período ya está cerrado")

        # =========================================================================
        # 1. LIMPIEZA DE CIERRES PREVIOS (Idempotencia)
        # =========================================================================
        patrones_cierre = [
            f"CIE-{periodo.nombre}",
            f"AJU-{periodo.nombre}",
            f"REV-{periodo.nombre}"
        ]
        stmt_buscar_previas = select(Partida).where(
            Partida.empresa_id == empresa_id,
            Partida.numero_poliza.in_(patrones_cierre)
        )
        result_previas = await db.execute(stmt_buscar_previas)
        partidas_previas = result_previas.scalars().all()
        if partidas_previas:
            ids_partidas_previas = [p.id for p in partidas_previas]
            await db.execute(delete(DetallePartida).where(DetallePartida.partida_id.in_(ids_partidas_previas)))
            await db.execute(delete(Partida).where(Partida.id.in_(ids_partidas_previas)))

        # =========================================================================
        # 2. PASO 1: Limpiar saldo ANTERIOR en "Utilidad del Período"
        # =========================================================================
        stmt_saldo_anterior = (
            select(
                func.coalesce(func.sum(case((DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto), else_=0)), 0).label('sum_debe'),
                func.coalesce(func.sum(case((DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto), else_=0)), 0).label('sum_haber')
            )
            .select_from(DetallePartida)
            .join(Partida, DetallePartida.partida_id == Partida.id)
            .where(
                DetallePartida.cuenta_id == empresa.cuenta_utilidad_periodo_id,
                Partida.fecha < periodo.fecha_inicio
            )
        )
        res_anterior = await db.execute(stmt_saldo_anterior)
        sum_debe_ant, sum_haber_ant = res_anterior.one()
        saldo_anterior = sum_debe_ant - sum_haber_ant
        poliza_ajuste_num = None
        
        if saldo_anterior != 0:
            schema_name = db.info["current_user"]["schema"]
            poliza_ajuste_num = await get_next_poliza(db, empresa_id, schema_name)
            partida_ajuste = Partida(
                fecha=periodo.fecha_fin,
                descripcion="AJUSTE PREVIO AL CIERRE: Traslado de saldo residual de Utilidad/Pérdida del Período a Utilidades Acumuladas",
                numero_poliza=f"AJU-{periodo.nombre}",
                empresa_id=empresa_id
            )
            db.add(partida_ajuste)
            await db.flush()
            if saldo_anterior > 0:
                db.add(DetallePartida(partida_id=partida_ajuste.id, cuenta_id=empresa.cuenta_utilidad_periodo_id, tipo_movimiento='haber', monto=abs(saldo_anterior)))
                db.add(DetallePartida(partida_id=partida_ajuste.id, cuenta_id=empresa.cuenta_utilidades_acumuladas_id, tipo_movimiento='debe', monto=abs(saldo_anterior)))
            else:
                monto_abs = abs(saldo_anterior)
                db.add(DetallePartida(partida_id=partida_ajuste.id, cuenta_id=empresa.cuenta_utilidad_periodo_id, tipo_movimiento='debe', monto=monto_abs))
                db.add(DetallePartida(partida_id=partida_ajuste.id, cuenta_id=empresa.cuenta_utilidades_acumuladas_id, tipo_movimiento='haber', monto=monto_abs))

        # =========================================================================
        # 3. PASO 2: Cierre de Cuentas Nominales
        # =========================================================================
        result_cuentas = await db.execute(
            select(CuentaContable).where(
                CuentaContable.empresa_id == empresa_id,
                CuentaContable.tipo.in_(['ingreso', 'gasto']),
                CuentaContable.is_active.is_(True)  # ✅ CORREGIDO: activa → is_active
            )
        )
        cuentas_nominales = result_cuentas.scalars().all()
        detalles_cierre = []
        total_ingresos = Decimal('0.00')
        total_gastos = Decimal('0.00')
        
        for cuenta in cuentas_nominales:
            stmt_saldo = (
                select(
                    func.coalesce(func.sum(case((DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto), else_=0)), 0).label('sum_debe'),
                    func.coalesce(func.sum(case((DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto), else_=0)), 0).label('sum_haber')
                )
                .select_from(DetallePartida)
                .join(Partida, DetallePartida.partida_id == Partida.id)
                .where(
                    DetallePartida.cuenta_id == cuenta.id,
                    Partida.fecha >= periodo.fecha_inicio,
                    Partida.fecha <= periodo.fecha_fin
                )
            )
            res_saldo = await db.execute(stmt_saldo)
            sum_debe, sum_haber = res_saldo.one()
            if sum_debe == sum_haber:
                continue
            if cuenta.tipo == 'ingreso':
                net_balance = sum_haber - sum_debe
                if net_balance != 0:
                    total_ingresos += net_balance
                    detalles_cierre.append({'cuenta_id': cuenta.id, 'tipo_movimiento': 'debe', 'monto': abs(net_balance)})
            elif cuenta.tipo == 'gasto':
                net_balance = sum_debe - sum_haber
                if net_balance != 0:
                    total_gastos += net_balance
                    detalles_cierre.append({'cuenta_id': cuenta.id, 'tipo_movimiento': 'haber', 'monto': abs(net_balance)})
        
        total_utilidad_periodo = total_ingresos - total_gastos
        poliza_cierre_num = None
        
        if detalles_cierre:
            schema_name = db.info["current_user"]["schema"]
            poliza_cierre_num = await get_next_poliza(db, empresa_id, schema_name)
            partida_cierre = Partida(
                fecha=periodo.fecha_fin,
                descripcion=f"CIERRE ANUAL: Cancelación de cuentas nominales (Ingresos y Gastos) - Período {periodo.nombre}",
                numero_poliza=f"CIE-{periodo.nombre}",
                empresa_id=empresa_id,
                tipo_origen='cierre',
            )
            db.add(partida_cierre)
            await db.flush()
            for det in detalles_cierre:
                db.add(DetallePartida(partida_id=partida_cierre.id, cuenta_id=det['cuenta_id'], tipo_movimiento=det['tipo_movimiento'], monto=det['monto']))
            if total_utilidad_periodo > 0:
                db.add(DetallePartida(partida_id=partida_cierre.id, cuenta_id=empresa.cuenta_utilidad_periodo_id, tipo_movimiento='haber', monto=total_utilidad_periodo))
            elif total_utilidad_periodo < 0:
                db.add(DetallePartida(partida_id=partida_cierre.id, cuenta_id=empresa.cuenta_utilidad_periodo_id, tipo_movimiento='debe', monto=abs(total_utilidad_periodo)))

        # =========================================================================
        # 4. PASO 3: Finalizar
        # =========================================================================
        periodo.cerrado = True
        await db.commit()
        return {
            "mensaje": f"Período {periodo.nombre} cerrado exitosamente",
            "poliza_ajuste_previo": poliza_ajuste_num,
            "poliza_cierre": poliza_cierre_num,
            "utilidad_neta_periodo": str(total_utilidad_periodo)
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al ejecutar el cierre: {str(e)}")