# app/services/reversion_cierre.py
from app.crud.secuencias import get_next_poliza
from app.models.tenant_models import DetallePartida, Partida, PeriodoFiscal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def revertir_cierre_anual(
    db: AsyncSession,
    empresa_id: int,  # ✅ BIGINT
    periodo_id: int   # ✅ BIGINT
) -> dict:
    try:
        # 1. Obtener y validar el período
        periodo = await db.get(PeriodoFiscal, periodo_id)
        if not periodo or periodo.empresa_id != empresa_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período fiscal no encontrado o no pertenece a la empresa.")
        if not periodo.cerrado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El período ya está abierto. No hay nada que revertir.")

        # 2. Verificar que no haya períodos posteriores cerrados
        stmt_posterior = select(PeriodoFiscal).where(
            PeriodoFiscal.empresa_id == empresa_id,
            PeriodoFiscal.fecha_inicio > periodo.fecha_inicio,
            PeriodoFiscal.cerrado.is_(True)
        )
        periodo_posterior_cerrado = (await db.execute(stmt_posterior)).scalar_one_or_none()
        if periodo_posterior_cerrado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede revertir este cierre porque el período '{periodo_posterior_cerrado.nombre}' ya está cerrado."
            )

        # 3. Validar que no exista ya una reversión (Idempotencia)
        patron_reversion = f"REV-{periodo.nombre}"
        stmt_rev_existente = select(Partida).where(
            Partida.empresa_id == empresa_id,
            Partida.numero_poliza == patron_reversion
        )
        if (await db.execute(stmt_rev_existente)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ya existe una partida de reversión '{patron_reversion}' para este período.")

        # 4. Obtener las partidas de cierre (CIE y AJU) CON SUS DETALLES
        patron_cierre = f"CIE-{periodo.nombre}"
        patron_ajuste = f"AJU-{periodo.nombre}"
        stmt_partidas_originales = (
            select(Partida)
            .options(selectinload(Partida.detalles))
            .where(
                Partida.empresa_id == empresa_id,
                Partida.numero_poliza.in_([patron_cierre, patron_ajuste])
            )
        )
        result = await db.execute(stmt_partidas_originales)
        partidas_originales = result.scalars().all()
        if not partidas_originales:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se encontraron partidas de cierre (CIE/AJU) para el período '{periodo.nombre}'.")

        # 5. Crear los detalles invertidos
        detalles_invertidos = []
        for partida_original in partidas_originales:
            for detalle in partida_original.detalles:
                tipo_invertido = 'haber' if detalle.tipo_movimiento == 'debe' else 'debe'
                detalles_invertidos.append({
                    'cuenta_id': detalle.cuenta_id,
                    'tipo_movimiento': tipo_invertido,
                    'monto': detalle.monto
                })
        if not detalles_invertidos:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Las partidas de cierre originales no tienen detalles activos para revertir.")

        # 6. Crear la partida de reversión (REV)
        schema_name = db.info["current_user"]["schema"]
        await get_next_poliza(db, empresa_id, schema_name)
        partida_rev = Partida(
            fecha=periodo.fecha_fin,
            descripcion=f"REVERSIÓN DE CIERRE CONTABLE - Período {periodo.nombre}. Contrarresta las pólizas {patron_cierre} y {patron_ajuste}.",
            numero_poliza=patron_reversion,
            empresa_id=empresa_id,
            tipo_origen='reversion_cierre',
        )
        db.add(partida_rev)
        await db.flush()
        for det in detalles_invertidos:
            db.add(DetallePartida(partida_id=partida_rev.id, cuenta_id=det['cuenta_id'], tipo_movimiento=det['tipo_movimiento'], monto=det['monto']))

        # 7. Reabrir el período
        periodo.cerrado = False
        await db.commit()
        return {
            "mensaje": f"El período '{periodo.nombre}' ha sido reabierto exitosamente.",
            "poliza_reversion": patron_reversion,
            "partidas_contrarrestadas": [p.numero_poliza for p in partidas_originales],
            "total_lineas_revertidas": len(detalles_invertidos),
            "periodo_id": periodo.id
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al revertir el cierre: {str(e)}")