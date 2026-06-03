import uuid
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
from app.schemas.activos_fijos import (
    ActivoFijoCreate,
    ActivoFijoUpdate,
    ProcesarDepreciacionMensualResponse,
    TablaDepreciacionProyectadaItem,
    TablaDepreciacionProyectadaResponse,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session

# ==============================================================================
# FUNCIONES AUXILIARES DE CÁLCULO
# ==============================================================================

def _redondear(monto: Decimal) -> Decimal:
    """Redondea a 2 decimales usando ROUND_HALF_UP (estándar contable)"""
    return monto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _calcular_depreciacion_mes(
    activo: ActivoFijo, 
    anio: int, 
    mes: int, 
    db: Session
) -> dict | None:
    """
    Calcula la depreciación para un activo en un mes específico.
    Retorna un diccionario con los montos o None si ya está depreciado o no aplica.
    """
    # 1. Verificar si ya existe registro para este periodo
    existe = db.query(DepreciacionActivo).filter(
        DepreciacionActivo.activo_id == activo.id,
        DepreciacionActivo.anio_periodo == anio,
        DepreciacionActivo.mes_periodo == mes
    ).first()
    
    if existe:
        return None # Ya fue procesado

    # 2. Verificar si el activo ya está totalmente depreciado o dado de baja
    if activo.estado in ['totalmente_depreciado', 'dado_baja', 'vendido']:
        return None

    # 3. Verificar si el periodo es anterior a la fecha de adquisición
    fecha_inicio_periodo = date(anio, mes, 1)
    if fecha_inicio_periodo < activo.fecha_adquisicion.replace(day=1):
        return None # Aún no comienza a depreciarse

    # 4. Calcular depreciación acumulada hasta el mes anterior
    depreciacion_acumulada_anterior = db.query(
        db.func.coalesce(db.func.sum(DepreciacionActivo.monto_depreciacion_mes), 0)
    ).filter(
        DepreciacionActivo.activo_id == activo.id,
        (DepreciacionActivo.anio_periodo < anio) | 
        ((DepreciacionActivo.anio_periodo == anio) & (DepreciacionActivo.mes_periodo < mes))
    ).scalar()

    # 5. Cálculo de línea recta
    base_depreciable = activo.valor_costo - activo.valor_residual
    depreciacion_mensual_estandar = base_depreciable / Decimal(activo.vida_util_meses_aplicada)
    depreciacion_mensual_estandar = _redondear(depreciacion_mensual_estandar)

    # 6. Ajuste del último mes: No depreciar más allá del valor residual
    depreciacion_acumulada_proyectada = depreciacion_acumulada_anterior + depreciacion_mensual_estandar
    
    if depreciacion_acumulada_proyectada >= base_depreciable:
        monto_a_depreciar = _redondear(base_depreciable - depreciacion_acumulada_anterior)
        if monto_a_depreciar <= 0:
            return None # Ya alcanzó el valor residual
    else:
        monto_a_depreciar = depreciacion_mensual_estandar

    nueva_depreciacion_acumulada = _redondear(depreciacion_acumulada_anterior + monto_a_depreciar)
    valor_en_libros = _redondear(activo.valor_costo - nueva_depreciacion_acumulada)

    return {
        "monto_depreciacion_mes": monto_a_depreciar,
        "depreciacion_acumulada_hasta_fecha": nueva_depreciacion_acumulada,
        "valor_en_libros": valor_en_libros
    }


# ==============================================================================
# SERVICIOS PRINCIPALES
# ==============================================================================

def crear_activo_fijo(db: Session, empresa_id: uuid.UUID, data: ActivoFijoCreate) -> ActivoFijo:
    # 1. Obtener categoría global para validar límites SAT
    categoria = db.query(CategoriaActivoFijo).filter(
        CategoriaActivoFijo.id == data.categoria_id,
        CategoriaActivoFijo.is_active == True
    ).first()
    
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria de activo no encontrada o inactiva")

    # 2. Validar tasa de depreciación contra el límite de la SAT
    if data.tasa_depreciacion_anual_aplicada > categoria.tasa_maxima_anual:
        raise HTTPException(
            status_code=400, 
            detail=f"La tasa aplicada ({data.tasa_depreciacion_anual_aplicada}%) excede el limite maximo de la SAT ({categoria.tasa_maxima_anual}%) para {categoria.nombre}."
        )

    # 3. Validar que se proporcionen cuentas contables (ya que no hay default en el catálogo global)
    if not data.cuenta_gasto_id or not data.cuenta_depreciacion_acumulada_id:
        raise HTTPException(
            status_code=400,
            detail="Es obligatorio especificar la cuenta de gasto y la cuenta de depreciacion acumulada al crear el activo."
        )

    # 4. Crear el registro
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
    db.commit()
    db.refresh(nuevo_activo)
    return nuevo_activo


def actualizar_activo_fijo(db: Session, activo_id: uuid.UUID, data: ActivoFijoUpdate) -> ActivoFijo:
    activo = db.query(ActivoFijo).filter(ActivoFijo.id == activo_id).first()
    if not activo:
        raise HTTPException(status_code=404, detail="Activo fijo no encontrado")

    # Si se actualiza la categoría o la tasa, revalidar contra la SAT
    if data.tasa_depreciacion_anual_aplicada is not None or data.categoria_id is not None:
        cat_id = data.categoria_id or activo.categoria_id
        categoria = db.query(CategoriaActivoFijo).filter(CategoriaActivoFijo.id == cat_id).first()
        
        tasa_a_validar = data.tasa_depreciacion_anual_aplicada or activo.tasa_depreciacion_anual_aplicada
        
        if categoria and tasa_a_validar > categoria.tasa_maxima_anual:
            raise HTTPException(
                status_code=400, 
                detail=f"La tasa excede el limite maximo de la SAT ({categoria.tasa_maxima_anual}%) para {categoria.nombre}."
            )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activo, field, value)

    db.commit()
    db.refresh(activo)
    return activo


def procesar_depreciacion_mensual(
    db: Session, 
    empresa_id: uuid.UUID, 
    anio: int, 
    mes: int
) -> ProcesarDepreciacionMensualResponse:
    """
    Procesa la depreciación de TODOS los activos de una empresa para un mes dado.
    Genera una única Partida de Diario consolidada en estado 'Borrador' (o el estado que tu sistema use).
    """
    # 1. Obtener activos elegibles
    activos = db.query(ActivoFijo).filter(
        ActivoFijo.empresa_id == empresa_id,
        ActivoFijo.estado == 'activo'
    ).all()

    if not activos:
        return ProcesarDepreciacionMensualResponse(
            exito=True,
            mensaje="No hay activos fijos activos para depreciar en este periodo.",
            activos_procesados=0,
            monto_total_depreciacion=Decimal('0.00'),
            partida_id_generada=None
        )

    # 2. Estructuras para agrupar la partida contable
    # Usamos un diccionario para sumar débitos y créditos por cuenta, evitando partidas infladas
    movimientos_debe: dict[uuid.UUID, Decimal] = {}
    movimientos_haber: dict[uuid.UUID, Decimal] = {}
    
    activos_procesados_count = 0
    monto_total = Decimal('0.00')
    registros_depreciacion_a_guardar: List[DepreciacionActivo] = []

    # 3. Procesar cada activo
    for activo in activos:
        calculo = _calcular_depreciacion_mes(activo, anio, mes, db)
        
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
                partida_id=None # Se llenará después de crear la partida
            )
            registros_depreciacion_a_guardar.append(reg_dep)

            # Acumular para la partida contable
            cuenta_gasto = activo.cuenta_gasto_id
            cuenta_dep_acum = activo.cuenta_depreciacion_acumulada_id

            movimientos_debe[cuenta_gasto] = movimientos_debe.get(cuenta_gasto, Decimal('0.00')) + monto_mes
            movimientos_haber[cuenta_dep_acum] = movimientos_haber.get(cuenta_dep_acum, Decimal('0.00')) + monto_mes

            # Actualizar estado si ya se depreció todo
            if calculo["valor_en_libros"] <= activo.valor_residual:
                activo.estado = 'totalmente_depreciado'

    # 4. Si no hubo depreciación que registrar, salir
    if activos_procesados_count == 0:
        return ProcesarDepreciacionMensualResponse(
            exito=True,
            mensaje="Los activos ya estaban totalmente depreciados o no corresponden a este periodo.",
            activos_procesados=0,
            monto_total_depreciacion=Decimal('0.00'),
            partida_id_generada=None
        )

    # 5. Generar la Partida de Diario Consolidada
    nueva_partida = Partida(
        empresa_id=empresa_id,
        fecha=date(anio, mes, 28), # Fecha convencional de cierre, ajustable
        descripcion=f"Depreciacion mensual de activos fijos - Periodo {mes:02d}/{anio}",
        numero_poliza=f"DEP-{anio}-{mes:02d}"
    )
    db.add(nueva_partida)
    db.flush() # Obtener el ID de la partida recién creada

    # 6. Crear los detalles de la partida (Débitos y Créditos)
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

    # 7. Vincular los registros de depreciación con la partida y guardar todo
    for reg_dep in registros_depreciacion_a_guardar:
        reg_dep.partida_id = nueva_partida.id
        db.add(reg_dep)

    db.commit()

    return ProcesarDepreciacionMensualResponse(
        exito=True,
        mensaje=f"Se procesaron {activos_procesados_count} activos. Partida #{nueva_partida.numero} generada en borrador.",
        activos_procesados=activos_procesados_count,
        monto_total_depreciacion=_redondear(monto_total),
        partida_id_generada=nueva_partida.id
    )


def obtener_proyeccion_depreciacion(db: Session, activo_id: uuid.UUID) -> TablaDepreciacionProyectadaResponse:
    """
    Genera una proyección futura de la depreciación para mostrar en el frontend.
    """
    activo = db.query(ActivoFijo).filter(ActivoFijo.id == activo_id).first()
    if not activo:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    # Obtener depreciación ya registrada
    historial = db.query(DepreciacionActivo).filter(
        DepreciacionActivo.activo_id == activo_id
    ).order_by(DepreciacionActivo.anio_periodo, DepreciacionActivo.mes_periodo).all()

    # Convertir a diccionario para búsqueda rápida
    historial_dict = {(h.anio_periodo, h.mes_periodo): h for h in historial}

    proyeccion: List[TablaDepreciacionProyectadaItem] = []
    
    depreciacion_acumulada_actual = Decimal('0.00')
    if historial:
        ultimo_registro = historial[-1]
        depreciacion_acumulada_actual = ultimo_registro.depreciacion_acumulada_hasta_fecha
        # Empezar la proyección desde el mes siguiente al último registrado
        anio_actual = ultimo_registro.anio_periodo
        mes_actual = ultimo_registro.mes_periodo + 1
        if mes_actual > 12:
            mes_actual = 1
            anio_actual += 1
    else:
        # Si no hay historial, empezar desde la fecha de adquisición
        anio_actual = activo.fecha_adquisicion.year
        mes_actual = activo.fecha_adquisicion.month

    base_depreciable = activo.valor_costo - activo.valor_residual
    depreciacion_mensual_estandar = _redondear(base_depreciable / Decimal(activo.vida_util_meses_aplicada))
    
    acumulado_proyectado = depreciacion_acumulada_actual

    # Proyectar hasta que se alcance el valor residual (con un límite de seguridad de iteraciones)
    iteraciones = 0
    max_iteraciones = activo.vida_util_meses_aplicada + 12

    while acumulado_proyectado < base_depreciable and iteraciones < max_iteraciones:
        iteraciones += 1
        
        # Verificar si ya existe en el historial real
        if (anio_actual, mes_actual) in historial_dict:
            reg = historial_dict[(anio_actual, mes_actual)]
            monto_mes = reg.monto_depreciacion_mes
            acumulado_proyectado = reg.depreciacion_acumulada_hasta_fecha
            valor_libros = reg.valor_en_libros
        else:
            # Calcular proyección
            monto_mes = depreciacion_mensual_estandar
            acumulado_proyectado_temp = acumulado_proyectado + monto_mes
            
            if acumulado_proyectado_temp >= base_depreciable:
                monto_mes = _redondear(base_depreciable - acumulado_proyectado)
            
            acumulado_proyectado = _redondear(acumulado_proyectado + monto_mes)
            valor_libros = _redondear(activo.valor_costo - acumulado_proyectado)

        proyeccion.append(TablaDepreciacionProyectadaItem(
            anio_periodo=anio_actual,
            mes_periodo=mes_actual,
            monto_depreciacion_mes=monto_mes,
            depreciacion_acumulada_hasta_fecha=acumulado_proyectado,
            valor_en_libros=valor_libros
        ))

        # Avanzar al siguiente mes
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