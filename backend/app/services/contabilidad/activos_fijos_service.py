# app/services/activos_fijos_service.py
import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import List

from app.models.global_models import CategoriaActivoFijo
from app.models.tenant_models import (
    ActivoFijo,
    DepreciacionActivo,
    DetallePartida,
    Partida,
)
from app.schemas.contabilidad.activos_fijos import (
    ActivoFijoCreate,
    ActivoFijoUpdate,
    ProcesarDepreciacionMensualResponse,
    TablaDepreciacionProyectadaItem,
    TablaDepreciacionProyectadaResponse,
)
from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


# ============================================================
# FUNCIONES AUXILIARES DE CÁLCULO
# ============================================================
def _redondear(monto: Decimal) -> Decimal:
    """Redondea a 2 decimales usando ROUND_HALF_UP (estándar contable guatemalteco)"""
    return monto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _dias_en_mes_adquisicion(fecha_adquisicion: date, anio: int, mes: int) -> int:
    """Calcula los días que el activo estuvo en uso durante el mes de adquisición."""
    _, ultimo_dia = calendar.monthrange(anio, mes)
    if fecha_adquisicion.year == anio and fecha_adquisicion.month == mes:
        return ultimo_dia - fecha_adquisicion.day + 1
    return ultimo_dia


def _dias_en_mes_final(fecha_adquisicion: date, vida_util_meses: int, anio: int, mes: int) -> int | None:
    """Calcula los días del mes final de la vida útil."""
    anio_fin = fecha_adquisicion.year + (fecha_adquisicion.month + vida_util_meses - 1) // 12
    mes_fin = (fecha_adquisicion.month + vida_util_meses - 1) % 12 + 1
    dia_fin = fecha_adquisicion.day
    
    if anio == anio_fin and mes == mes_fin:
        return dia_fin - 1
    return None


async def _calcular_depreciacion_mes(
    activo: ActivoFijo,
    anio: int,
    mes: int,
    db: AsyncSession
) -> dict | None:
    """Calcula la depreciación para un activo en un mes específico."""
    # 1. Verificar si ya existe registro
    stmt = select(DepreciacionActivo).where(
        DepreciacionActivo.activo_id == activo.id,
        DepreciacionActivo.anio_periodo == anio,
        DepreciacionActivo.mes_periodo == mes
    )
    result = await db.execute(stmt)
    existe = result.scalar_one_or_none()
    if existe:
        return None
    
    # 2. Verificar estado del activo
    if activo.estado in ['totalmente_depreciado', 'dado_baja', 'vendido']:
        return None
    
    # 3. Verificar período
    fecha_inicio_periodo = date(anio, mes, 1)
    if fecha_inicio_periodo < activo.fecha_adquisicion.replace(day=1):
        return None
    
    # 4. Calcular depreciación acumulada
    stmt = select(func.coalesce(func.sum(DepreciacionActivo.monto_depreciacion_mes), 0)).where(
        DepreciacionActivo.activo_id == activo.id,
        or_(
            DepreciacionActivo.anio_periodo < anio,
            and_(
                DepreciacionActivo.anio_periodo == anio,
                DepreciacionActivo.mes_periodo < mes
            )
        )
    )
    result = await db.execute(stmt)
    depreciacion_acumulada_anterior = result.scalar_one() or Decimal('0.00')
    
    # 5. Cálculo base
    base_depreciable = activo.valor_costo - activo.valor_residual
    depreciacion_mensual_estandar = _redondear(
        base_depreciable / Decimal(activo.vida_util_meses_aplicada)
    )
    _, dias_del_mes = calendar.monthrange(anio, mes)
    
    # 6. Determinar si es primer o último mes
    es_primer_mes = (activo.fecha_adquisicion.year == anio and activo.fecha_adquisicion.month == mes)
    dias_mes_final = _dias_en_mes_final(activo.fecha_adquisicion, activo.vida_util_meses_aplicada, anio, mes)
    es_ultimo_mes = dias_mes_final is not None
    
    # 7. Calcular monto
    if es_primer_mes:
        dias_uso = _dias_en_mes_adquisicion(activo.fecha_adquisicion, anio, mes)
        factor = Decimal(dias_uso) / Decimal(dias_del_mes)
        monto_a_depreciar = _redondear(depreciacion_mensual_estandar * factor)
    elif es_ultimo_mes:
        monto_a_depreciar = _redondear(base_depreciable - depreciacion_acumulada_anterior)
    else:
        monto_a_depreciar = depreciacion_mensual_estandar
    
    # 8. Validar
    if monto_a_depreciar <= 0:
        return None
    if depreciacion_acumulada_anterior + monto_a_depreciar > base_depreciable:
        monto_a_depreciar = _redondear(base_depreciable - depreciacion_acumulada_anterior)
        if monto_a_depreciar <= 0:
            return None
    
    # 9. Calcular acumulados
    nueva_depreciacion_acumulada = _redondear(depreciacion_acumulada_anterior + monto_a_depreciar)
    valor_en_libros = _redondear(activo.valor_costo - nueva_depreciacion_acumulada)
    
    return {
        "monto_depreciacion_mes": monto_a_depreciar,
        "depreciacion_acumulada_hasta_fecha": nueva_depreciacion_acumulada,
        "valor_en_libros": valor_en_libros,
        "es_primer_mes": es_primer_mes,
        "es_ultimo_mes": es_ultimo_mes,
        "dias_usados": dias_uso if es_primer_mes else (dias_mes_final if es_ultimo_mes else dias_del_mes),
        "dias_del_mes": dias_del_mes
    }


# ============================================================
# SERVICIOS PRINCIPALES
# ============================================================
async def crear_activo_fijo_async(db: AsyncSession, empresa_id: int, data: ActivoFijoCreate) -> ActivoFijo:  # ✅ BIGINT
    """Crea un nuevo activo fijo."""
    # 1. Validar categoría
    stmt = select(CategoriaActivoFijo).where(
        CategoriaActivoFijo.id == data.categoria_id,
        CategoriaActivoFijo.is_active.is_(True)
    )
    result = await db.execute(stmt)
    categoria = result.scalar_one_or_none()
    
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria de activo no encontrada o inactiva")
    
    # 2. Validar tasa
    if data.tasa_depreciacion_anual_aplicada > categoria.tasa_maxima_anual:
        raise HTTPException(
            status_code=400,
            detail=f"La tasa aplicada ({data.tasa_depreciacion_anual_aplicada}%) excede el limite maximo de la SAT ({categoria.tasa_maxima_anual}%) para {categoria.nombre}."
        )
    
    # 3. Validar cuentas
    if not data.cuenta_gasto_id or not data.cuenta_depreciacion_acumulada_id:
        raise HTTPException(
            status_code=400,
            detail="Es obligatorio especificar la cuenta de gasto y la cuenta de depreciacion acumulada al crear el activo."
        )
    
    # 4. Crear registro
    nuevo_activo = ActivoFijo(
        empresa_id=empresa_id,
        categoria_id=data.categoria_id,
        codigo_interno=data.codigo_interno,
        descripcion=data.descripcion,
        fecha_adquisicion=data.fecha_adquisicion,
        valor_costo=data.valor_costo,
        valor_residual=data.valor_residual,
        tasa_depreciacion_anual_aplicada=data.tasa_depreciacion_anual_aplicada,
        vida_util_meses_aplicada=data.vida_util_meses_aplicada,
        cuenta_gasto_id=data.cuenta_gasto_id,
        cuenta_depreciacion_acumulada_id=data.cuenta_depreciacion_acumulada_id,
        estado=data.estado
    )
    db.add(nuevo_activo)
    await db.flush()
    
    # 5. Recargar con relaciones
    stmt = select(ActivoFijo).options(
        selectinload(ActivoFijo.categoria),
        selectinload(ActivoFijo.cuenta_gasto),
        selectinload(ActivoFijo.cuenta_depreciacion_acumulada)
    ).where(ActivoFijo.id == nuevo_activo.id)
    result = await db.execute(stmt)
    activo_con_relaciones = result.scalar_one()
    
    await db.commit()
    return activo_con_relaciones


async def actualizar_activo_fijo_async(db: AsyncSession, activo_id: int, data: ActivoFijoUpdate) -> ActivoFijo:  # ✅ BIGINT
    """Actualiza un activo fijo existente."""
    stmt = select(ActivoFijo).where(ActivoFijo.id == activo_id)
    result = await db.execute(stmt)
    activo = result.scalar_one_or_none()
    
    if not activo:
        raise HTTPException(status_code=404, detail="Activo fijo no encontrado")
    
    # Si se actualiza la categoría o la tasa, revalidar
    if data.tasa_depreciacion_anual_aplicada is not None or data.categoria_id is not None:
        cat_id = data.categoria_id or activo.categoria_id
        stmt_cat = select(CategoriaActivoFijo).where(CategoriaActivoFijo.id == cat_id)
        result_cat = await db.execute(stmt_cat)
        categoria = result_cat.scalar_one_or_none()
        
        tasa_a_validar = data.tasa_depreciacion_anual_aplicada or activo.tasa_depreciacion_anual_aplicada
        if categoria and tasa_a_validar > categoria.tasa_maxima_anual:
            raise HTTPException(
                status_code=400,
                detail=f"La tasa excede el limite maximo de la SAT ({categoria.tasa_maxima_anual}%) para {categoria.nombre}."
            )
    
    # Actualizar campos
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activo, field, value)
    
    await db.flush()
    
    # Recargar con relaciones
    stmt = select(ActivoFijo).options(
        selectinload(ActivoFijo.categoria),
        selectinload(ActivoFijo.cuenta_gasto),
        selectinload(ActivoFijo.cuenta_depreciacion_acumulada)
    ).where(ActivoFijo.id == activo_id)
    result = await db.execute(stmt)
    activo_con_relaciones = result.scalar_one()
    
    await db.commit()
    return activo_con_relaciones


async def procesar_depreciacion_mensual_async(
    db: AsyncSession,
    empresa_id: int,  # ✅ BIGINT
    anio: int,
    mes: int
) -> ProcesarDepreciacionMensualResponse:
    """Procesa la depreciación de TODOS los activos de una empresa para un mes dado."""
    # 1. Obtener activos elegibles
    stmt = select(ActivoFijo).where(
        ActivoFijo.empresa_id == empresa_id,
        ActivoFijo.estado == 'activo'
    )
    result = await db.execute(stmt)
    activos = result.scalars().all()
    
    if not activos:
        return ProcesarDepreciacionMensualResponse(
            exito=True,
            mensaje="No hay activos fijos activos para depreciar en este periodo.",
            activos_procesados=0,
            monto_total_depreciacion=Decimal('0.00'),
            partida_id_generada=None
        )
    
    # 2. Estructuras para agrupar
    movimientos_debe: dict[int, Decimal] = {}
    movimientos_haber: dict[int, Decimal] = {}
    activos_procesados_count = 0
    monto_total = Decimal('0.00')
    registros_depreciacion_a_guardar: List[DepreciacionActivo] = []
    
    # 3. Procesar cada activo
    for activo in activos:
        calculo = await _calcular_depreciacion_mes(activo, anio, mes, db)
        if calculo and calculo["monto_depreciacion_mes"] > 0:
            monto_mes = calculo["monto_depreciacion_mes"]
            monto_total += monto_mes
            activos_procesados_count += 1
            
            # Crear registro histórico
            reg_dep = DepreciacionActivo(
                empresa_id=empresa_id,
                activo_id=activo.id,
                anio_periodo=anio,
                mes_periodo=mes,
                monto_depreciacion_mes=monto_mes,
                depreciacion_acumulada_hasta_fecha=calculo["depreciacion_acumulada_hasta_fecha"],
                valor_en_libros=calculo["valor_en_libros"],
                partida_id=None
            )
            registros_depreciacion_a_guardar.append(reg_dep)
            
            # Acumular para la partida
            cuenta_gasto = activo.cuenta_gasto_id
            cuenta_dep_acum = activo.cuenta_depreciacion_acumulada_id
            movimientos_debe[cuenta_gasto] = movimientos_debe.get(cuenta_gasto, Decimal('0.00')) + monto_mes
            movimientos_haber[cuenta_dep_acum] = movimientos_haber.get(cuenta_dep_acum, Decimal('0.00')) + monto_mes
            
            # Actualizar estado si está totalmente depreciado
            if calculo["valor_en_libros"] <= activo.valor_residual:
                activo.estado = 'totalmente_depreciado'
    
    # 4. Si no hubo depreciación
    if activos_procesados_count == 0:
        return ProcesarDepreciacionMensualResponse(
            exito=True,
            mensaje="Los activos ya estaban totalmente depreciados o no corresponden a este periodo.",
            activos_procesados=0,
            monto_total_depreciacion=Decimal('0.00'),
            partida_id_generada=None
        )
    
    # 5. Generar Partida de Diario
    nueva_partida = Partida(
        empresa_id=empresa_id,
        fecha=date(anio, mes, 28),
        descripcion=f"Depreciacion mensual de activos fijos - Periodo {mes:02d}/{anio}",
        numero_poliza=f"DEP-{anio}-{mes:02d}"
    )
    db.add(nueva_partida)
    await db.flush()
    
    # 6. Crear detalles de la partida
    for cuenta_id, monto in movimientos_debe.items():
        db.add(DetallePartida(
            partida_id=nueva_partida.id,
            cuenta_id=cuenta_id,
            tipo_movimiento="debe",
            monto=monto
        ))
    
    for cuenta_id, monto in movimientos_haber.items():
        db.add(DetallePartida(
            partida_id=nueva_partida.id,
            cuenta_id=cuenta_id,
            tipo_movimiento="haber",
            monto=monto
        ))
    
    # 7. Vincular registros de depreciación con la partida
    for reg_dep in registros_depreciacion_a_guardar:
        reg_dep.partida_id = nueva_partida.id
        db.add(reg_dep)
    
    await db.commit()
    
    return ProcesarDepreciacionMensualResponse(
        exito=True,
        mensaje=f"Se procesaron {activos_procesados_count} activos. Partida #{nueva_partida.numero_poliza} generada.",
        activos_procesados=activos_procesados_count,
        monto_total_depreciacion=_redondear(monto_total),
        partida_id_generada=nueva_partida.id
    )


async def obtener_proyeccion_depreciacion_async(db: AsyncSession, activo_id: int) -> TablaDepreciacionProyectadaResponse:  # ✅ BIGINT
    """Genera una proyección futura de la depreciación."""
    stmt = select(ActivoFijo).where(ActivoFijo.id == activo_id)
    result = await db.execute(stmt)
    activo = result.scalar_one_or_none()
    
    if not activo:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    
    # Obtener depreciación ya registrada
    stmt = select(DepreciacionActivo).where(
        DepreciacionActivo.activo_id == activo_id
    ).order_by(DepreciacionActivo.anio_periodo, DepreciacionActivo.mes_periodo)
    result = await db.execute(stmt)
    historial = result.scalars().all()
    
    # Convertir a diccionario
    historial_dict = {(h.anio_periodo, h.mes_periodo): h for h in historial}
    
    proyeccion: List[TablaDepreciacionProyectadaItem] = []
    depreciacion_acumulada_actual = Decimal('0.00')
    
    if historial:
        ultimo_registro = historial[-1]
        depreciacion_acumulada_actual = ultimo_registro.depreciacion_acumulada_hasta_fecha
        anio_actual = ultimo_registro.anio_periodo
        mes_actual = ultimo_registro.mes_periodo + 1
        if mes_actual > 12:
            mes_actual = 1
            anio_actual += 1
    else:
        anio_actual = activo.fecha_adquisicion.year
        mes_actual = activo.fecha_adquisicion.month
    
    base_depreciable = activo.valor_costo - activo.valor_residual
    depreciacion_mensual_estandar = _redondear(
        base_depreciable / Decimal(activo.vida_util_meses_aplicada)
    )
    
    acumulado_proyectado = depreciacion_acumulada_actual
    fecha_actual = date.today()
    iteraciones = 0
    max_iteraciones = activo.vida_util_meses_aplicada + 12
    
    while acumulado_proyectado < base_depreciable and iteraciones < max_iteraciones:
        iteraciones += 1
        _, dias_del_mes = calendar.monthrange(anio_actual, mes_actual)
        
        if (anio_actual, mes_actual) in historial_dict:
            reg = historial_dict[(anio_actual, mes_actual)]
            monto_mes = reg.monto_depreciacion_mes
            acumulado_proyectado = reg.depreciacion_acumulada_hasta_fecha
            valor_libros = reg.valor_en_libros
            es_historico = True
            nota = None
        else:
            es_primer_mes = (activo.fecha_adquisicion.year == anio_actual and activo.fecha_adquisicion.month == mes_actual)
            dias_mes_final = _dias_en_mes_final(activo.fecha_adquisicion, activo.vida_util_meses_aplicada, anio_actual, mes_actual)
            es_ultimo_mes = dias_mes_final is not None
            
            if es_primer_mes:
                dias_uso = _dias_en_mes_adquisicion(activo.fecha_adquisicion, anio_actual, mes_actual)
                factor = Decimal(dias_uso) / Decimal(dias_del_mes)
                monto_mes = _redondear(depreciacion_mensual_estandar * factor)
                nota = f"Prorrateo: {dias_uso}/{dias_del_mes} días"
            elif es_ultimo_mes:
                monto_mes = _redondear(base_depreciable - acumulado_proyectado)
                nota = f"Ajuste final: {dias_mes_final} días"
            else:
                monto_mes = depreciacion_mensual_estandar
                nota = None
            
            if acumulado_proyectado + monto_mes > base_depreciable:
                monto_mes = _redondear(base_depreciable - acumulado_proyectado)
            
            acumulado_proyectado = _redondear(acumulado_proyectado + monto_mes)
            valor_libros = _redondear(activo.valor_costo - acumulado_proyectado)
            
            fecha_fin_mes = date(anio_actual, mes_actual, dias_del_mes)
            es_historico = fecha_fin_mes <= fecha_actual
        
        proyeccion.append(TablaDepreciacionProyectadaItem(
            anio_periodo=anio_actual,
            mes_periodo=mes_actual,
            monto_depreciacion_mes=monto_mes,
            depreciacion_acumulada_hasta_fecha=acumulado_proyectado,
            valor_en_libros=valor_libros,
            es_historico=es_historico,
            nota=nota
        ))
        
        mes_actual += 1
        if mes_actual > 12:
            mes_actual = 1
            anio_actual += 1
    
    return TablaDepreciacionProyectadaResponse(
        activo_id=activo.id,
        codigo_interno=activo.codigo_interno,
        descripcion=activo.descripcion,
        valor_costo=activo.valor_costo,
        valor_residual=activo.valor_residual,
        proyeccion=proyeccion
    )