# app/services/sat_libros_service.py
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.models.global_models import EstadoLibro, RegimenFiscal, TipoLibro
from app.models.tenant_models import (
    FacturaElectronica,
    SatLibro,
    SatLibroLinea,
)
from app.schemas.sat_libros import SatLibroCreate
from fastapi import HTTPException, status
from sqlalchemy import delete, extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def procesar_y_generar_libro_sat(
    db: AsyncSession, 
    payload: SatLibroCreate
) -> SatLibro:
    """
    Motor que extrae datos de FacturaElectronica mapeando dinámicamente
    totales, emisores/receptores y reglas impositivas de la SAT.
    """
    anio = payload.anio_periodo
    mes = payload.mes_periodo
    empresa_id = payload.empresa_id
    
    # Mapeo semántico al campo 'tipo_operacion' de tu FacturaElectronica ('Compra' o 'Venta')
    # Usamos capitalize() ya que el default en tu modelo es 'Compra'
    tipo_operacion_db = "Compra" if payload.tipo_libro == TipoLibro.COMPRAS else "Venta"

    # 1. Validar existencia y estado del libro en el tenant
    query_existente = select(SatLibro).where(
        SatLibro.empresa_id == empresa_id,
        SatLibro.tipo_libro == payload.tipo_libro,
        SatLibro.anio_periodo == anio,
        SatLibro.mes_periodo == mes
    )
    result_existente = await db.execute(query_existente)
    libro_existente = result_existente.scalar_one_or_none()

    if libro_existente:
        if libro_existente.estado in [EstadoLibro.FINALIZADO, EstadoLibro.PRESENTADO]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El libro seleccionado ya se encuentra bajo el estado '{libro_existente.estado.value}' y no puede modificarse."
            )
        # Limpieza de registros correlativos previos (Idempotencia)
        await db.execute(delete(SatLibroLinea).where(SatLibroLinea.libro_id == libro_existente.id))
        libro = libro_existente
    else:
        libro = SatLibro(
            id=uuid4(),
            empresa_id=empresa_id,
            tipo_libro=payload.tipo_libro,
            regimen_fiscal=payload.regimen_fiscal,
            anio_periodo=anio,
            mes_periodo=mes,
            estado=EstadoLibro.BORRADOR
        )
        db.add(libro)

    # 2. Query optimizado a las facturas electrónicas activas del periodo
    query_facturas = select(FacturaElectronica).where(
        FacturaElectronica.empresa_id == empresa_id,
        func.lower(FacturaElectronica.tipo_operacion) == tipo_operacion_db.lower(),
        func.lower(FacturaElectronica.estado) == "activa",
        extract('year', FacturaElectronica.fecha_emision) == anio,
        extract('month', FacturaElectronica.fecha_emision) == mes
    ).order_by(FacturaElectronica.fecha_emision.asc())
    
    result_facturas = await db.execute(query_facturas)
    facturas = result_facturas.scalars().all()

    # Acumuladores contables
    total_lineas = 0
    acum_exento = Decimal("0.00")
    acum_base = Decimal("0.00")
    acum_iva = Decimal("0.00")
    acum_monto = Decimal("0.00")
    lineas_a_insertar = []

    # 3. Transformación y desglose de rubros SAT
    for idx, fac in enumerate(facturas, start=1):
        total_lineas += 1
        
        # Asignación de procedencia de NIT y Razón Social según corresponda al libro
        if payload.tipo_libro == TipoLibro.COMPRAS:
            nit_linea = fac.emisor_nit
            razon_social_linea = fac.emisor_nombre
        else:
            nit_linea = fac.receptor_nit
            razon_social_linea = fac.receptor_nombre

        # Formatear el número de documento (Serie + Correlativo si existe la serie)
        doc_identificador = f"{fac.serie} - {fac.numero}" if fac.serie else fac.numero

        # Determinación de Créditos y Débitos del Régimen General
        es_regimen_general = payload.regimen_fiscal == RegimenFiscal.GENERAL
        credito_calc = fac.total_iva if (payload.tipo_libro == TipoLibro.COMPRAS and es_regimen_general) else Decimal("0.00")
        debito_calc = fac.total_iva if (payload.tipo_libro == TipoLibro.VENTAS and es_regimen_general) else Decimal("0.00")

        # Incrementos globales
        acum_base += fac.total_gravado
        acum_iva += fac.total_iva
        acum_monto += fac.total
        acum_exento += fac.total_exento

        # 1. Normalización a GTQ
        tc = float(fac.tipo_cambio or 1.0)
        monto_total_gtq = float(fac.total) * tc
        
        # 2. Clasificación lógica
        if fac.total_iva == 0.00:
            # Exportaciones o exentas van a la nueva columna
            linea_data = {
                "monto_exento": Decimal(str(monto_total_gtq)),
                "base_imponible": Decimal("0.00"),
                "monto_iva": Decimal("0.00")
            }
        else:
            # Operaciones normales gravadas
            linea_data = {
                "monto_exento": Decimal("0.00"),
                "base_imponible": Decimal(str(float(fac.total_gravado) * tc)),
                "monto_iva": Decimal(str(float(fac.total_iva) * tc))
            }

        nueva_linea = SatLibroLinea(
            id=uuid4(),
            libro_id=libro.id,
            factura_id=fac.id,
            numero_secuencia=idx,
            fecha_documento=fac.fecha_emision.date(),  # Conversión explícita de DateTime a Date
            numero_documento=doc_identificador[:50],   # Control de overflow del String(50)
            nit=nit_linea,
            razon_social=razon_social_linea,
            es_exento=fac.total_exento > 0,
            monto_total=Decimal(str(monto_total_gtq)),
            credito_fiscal=credito_calc,
            debito_fiscal=debito_calc,
            **linea_data
        )
        lineas_a_insertar.append(nueva_linea)

    if lineas_a_insertar:
        db.add_all(lineas_a_insertar)

    # 4. Asignación de sumatorias calculadas al encabezado
    libro.total_lineas = total_lineas
    libro.total_exento = acum_exento
    libro.total_base_imponible = acum_base
    libro.total_iva = acum_iva
    libro.total_monto = acum_monto
    libro.creado_el = datetime.utcnow()

    await db.commit()
    await db.refresh(libro)
    return libro

async def obtener_libro_detallado(
    db: AsyncSession,
    empresa_id: UUID,
    tipo_libro: TipoLibro,
    anio: int,
    mes: int
) -> SatLibro | None:
    """
    Busca un libro por sus parámetros de periodo y carga todas sus líneas
    asociadas de forma ordenada para el consumo del Frontend.
    """
    query = (
        select(SatLibro)
        .where(
            SatLibro.empresa_id == empresa_id,
            SatLibro.tipo_libro == tipo_libro,
            SatLibro.anio_periodo == anio,
            SatLibro.mes_periodo == mes
        )
        .options(selectinload(SatLibro.lineas)) # 🧠 Carga eager asíncrona optimizada
    )
    
    result = await db.execute(query)
    libro = result.scalar_one_or_none()
    
    if libro:
        # Ordenamos las líneas por su número correlativo de secuencia antes de enviarlas
        libro.lineas.sort(key=lambda x: x.numero_secuencia)
        
    return libro


async def finalizar_libro_sat(
    db: AsyncSession,
    libro_id: UUID,
    usuario_id: UUID
) -> SatLibro:
    """
    Cambia el estado de un libro de 'borrador' a 'finalizado', 
    registrando la auditoría de quién lo hizo y cuándo.
    """
    query = select(SatLibro).where(SatLibro.id == libro_id).options(selectinload(SatLibro.lineas))
    result = await db.execute(query)
    libro = result.scalar_one_or_none()
    
    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El libro contable solicitado no existe."
        )
        
    if libro.estado != EstadoLibro.BORRADOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede finalizar un libro que ya está en estado '{libro.estado.value}'."
        )
        
    # Cambiamos estado y estampamos auditoría
    libro.estado = EstadoLibro.FINALIZADO
    libro.finalizado_por = usuario_id
    libro.finalizado_el = datetime.utcnow()
    
    await db.commit()
    await db.refresh(libro)
    return libro