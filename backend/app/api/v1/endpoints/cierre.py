# app/api/v1/endpoints/cierre.py
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.crud.secuencias import get_next_poliza
from app.db.session import get_public_db
from app.models.tenant_models import (
    CuentaContable,
    DetallePartida,
    Partida,
    PeriodoFiscal,
)

router = APIRouter()

# ==========================================
# Helper: Configurar search_path según rol
# ==========================================
async def _set_schema_for_query(db: AsyncSession, scope: DataScope, tenant_id: str | None = None):
    """Configura el search_path correcto según el rol del usuario."""
    schema_name = None
    
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": tenant_id}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": str(scope.tenant_id)}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]

    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name

# ==========================================
# 1. Ejecutar Cierre Anual
# ==========================================
@router.post("/cierre-anual", response_model=dict, status_code=status.HTTP_201_CREATED)
async def cierre_anual(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    periodo_id: UUID = Query(..., description="ID del período fiscal a cerrar"),
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    # 1. Validar período
    result = await db.execute(
        select(PeriodoFiscal).where(
            PeriodoFiscal.id == periodo_id,
            PeriodoFiscal.empresa_id == empresa_id
        )
    )
    periodo = result.scalar_one_or_none()
    if not periodo:
        raise HTTPException(status_code=400, detail="Período fiscal no encontrado")
    if periodo.cerrado:
        raise HTTPException(status_code=400, detail="El período ya está cerrado")

    # 2. Obtener cuentas de resultado (ingresos y gastos) de la empresa
    result = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == empresa_id,
            CuentaContable.tipo.in_(['ingreso', 'gasto']),
            CuentaContable.activa == True
        )
    )
    cuentas_resultado = result.scalars().all()

    if not cuentas_resultado:
        raise HTTPException(status_code=400, detail="No hay cuentas de resultado para esta empresa")

    # 3. Obtener la cuenta de cierre: "Utilidad o Pérdida del Ejercicio" (código 3.4)
    result_cuenta_cierre = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == empresa_id,
            CuentaContable.codigo == "3.4"
        )
    )
    cuenta_cierre = result_cuenta_cierre.scalar_one_or_none()
    if not cuenta_cierre:
        raise HTTPException(status_code=400, detail="No existe la cuenta 3.4 (Utilidad o Pérdida del Ejercicio)")

    # 4. Calcular saldos de cada cuenta de resultado en el período
    detalles_cierre = []
    total_utilidad = Decimal('0.00')

    for cuenta in cuentas_resultado:
        stmt = (select(
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto), else_=0)
                    ), 0).label('sum_debe'),
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto), else_=0)
                    ), 0).label('sum_haber'))
                .select_from(DetallePartida)
                .join(Partida, DetallePartida.partida_id == Partida.id)
                .where(
                    DetallePartida.cuenta_id == cuenta.id,
                    Partida.fecha >= periodo.fecha_inicio,
                    Partida.fecha <= periodo.fecha_fin
                ))

        result_sum = await db.execute(stmt)
        sum_debe, sum_haber = result_sum.one()

        if cuenta.naturaleza == 'deudora':
            saldo = sum_debe - sum_haber
        else:
            saldo = sum_haber - sum_debe

        if saldo == 0:
            continue

        if saldo > 0:
            if cuenta.naturaleza == 'deudora':
                tipo_cierre = 'haber'
            else:
                tipo_cierre = 'debe'
        else:
            saldo = abs(saldo)
            if cuenta.naturaleza == 'deudora':
                tipo_cierre = 'debe'
            else:
                tipo_cierre = 'haber'

        detalles_cierre.append({
            'cuenta_id': cuenta.id,
            'tipo_movimiento': tipo_cierre,
            'monto': saldo
        })

        if cuenta.tipo == 'ingreso':
            if cuenta.naturaleza == 'acreedora':
                total_utilidad += (sum_haber - sum_debe)
            else:
                total_utilidad += (sum_debe - sum_haber)
        else:
            if cuenta.naturaleza == 'deudora':
                total_utilidad -= (sum_debe - sum_haber)
            else:
                total_utilidad -= (sum_haber - sum_debe)

    # 5. Crear partida de cierre de resultados
    if detalles_cierre:
        if total_utilidad > 0:
            tipo_cierre_utilidad = 'haber'
        else:
            tipo_cierre_utilidad = 'debe'
            total_utilidad = abs(total_utilidad)

        detalles_cierre.append({
            'cuenta_id': cuenta_cierre.id,
            'tipo_movimiento': tipo_cierre_utilidad,
            'monto': total_utilidad
        })

        numero_poliza = await get_next_poliza(db, empresa_id)

        partida_cierre = Partida(
            fecha=periodo.fecha_fin,
            descripcion=f"Cierre de resultados - Período {periodo.nombre}",
            numero_poliza=f"CIE-{periodo.nombre}"
        )
        db.add(partida_cierre)
        await db.flush()

        for det in detalles_cierre:
            db.add(DetallePartida(
                partida_id=partida_cierre.id,
                cuenta_id=det['cuenta_id'],
                tipo_movimiento=det['tipo_movimiento'],
                monto=det['monto']
            ))

        await db.commit()

    # 6. Segunda etapa: Cierre de "Utilidad del Ejercicio" contra "Utilidades Acumuladas"
    if total_utilidad != 0:
        result_acum = await db.execute(
            select(CuentaContable).where(
                CuentaContable.empresa_id == empresa_id,
                CuentaContable.codigo == "3.3.1"
            )
        )
        cuenta_acumulada = result_acum.scalar_one_or_none()
        if not cuenta_acumulada:
            raise HTTPException(status_code=400, detail="No existe la cuenta 3.3.1 (Utilidades/Pérdidas Acumuladas)")

        tipo_cierre_acum = 'debe' if tipo_cierre_utilidad == 'haber' else 'haber'
        numero_poliza_acum = await get_next_poliza(db, empresa_id)

        partida_acum = Partida(
            fecha=periodo.fecha_fin,
            descripcion=f"Traslado de utilidad a acumulada - Período {periodo.nombre}",
            numero_poliza=f"ACUM-{periodo.nombre}"
        )
        db.add(partida_acum)
        await db.flush()

        db.add(DetallePartida(
            partida_id=partida_acum.id,
            cuenta_id=cuenta_cierre.id,
            tipo_movimiento=tipo_cierre_acum,
            monto=total_utilidad
        ))
        db.add(DetallePartida(
            partida_id=partida_acum.id,
            cuenta_id=cuenta_acumulada.id,
            tipo_movimiento=tipo_cierre_utilidad,
            monto=total_utilidad
        ))

    # 7. Marcar el período como cerrado
    periodo.cerrado = True
    await db.commit()

    return {
        "mensaje": f"Período {periodo.nombre} cerrado exitosamente",
        "utilidad_neta": str(total_utilidad),
        "cuenta_cierre": cuenta_cierre.codigo,
        "cuenta_acumulada": cuenta_acumulada.codigo if total_utilidad != 0 else None
    }